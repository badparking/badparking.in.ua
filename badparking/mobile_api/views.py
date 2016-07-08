import logging
import facebook

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import viewsets, permissions, response, generics, exceptions, mixins, status
from rest_framework.decorators import detail_route

from core.models import CrimeType, Claim
from profiles.serializers import UserSerializer
from profiles.jwt import jwt_from_user
from .serializers import ClaimSerializer, CrimeTypeSerializer, UserCompleteSerializer, FacebookAuthUserSerializer
from .models import Client
from .mixins import ClientAuthMixin, UserObjectMixin, ClaimCreateMixin


logger = logging.getLogger(__name__)
User = get_user_model()


class CrimeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve crime types.
    """
    queryset = CrimeType.objects.filter(enabled=True)
    serializer_class = CrimeTypeSerializer
    permission_classes = (permissions.AllowAny,)


class CurrentUserView(UserObjectMixin, generics.RetrieveAPIView):
    """
    Retrieve current authenticated user info.
    """
    serializer_class = UserSerializer


class CompleteCurrentUserView(UserObjectMixin, generics.UpdateAPIView):
    """
    Update current authenticated user with required fields that could not be obtained during registration.
    """
    serializer_class = UserCompleteSerializer


class FacebookAuthUserView(ClientAuthMixin, generics.GenericAPIView):
    FACEBOOK_API_VERSION = '2.5'
    FACEBOOK_USER_FIELDS = 'id,email,first_name,last_name,middle_name'

    serializer_class = FacebookAuthUserSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        Authenticate user with Facebook `access_token` as provided by the client.

        May create a new user if there was none yet or update existing.
        Requires client authentication by client id and secret pair.
        ---
        parameters:
            - name: client_id
              description: ID of the API Client
              required: true
              type: string
              paramType: query
            - name: client_secret
              description: Secret of the API Client hashed with a timestamp as `SHA256(secret + timestamp)`
              required: true
              type: string
              paramType: query
            - name: timestamp
              description: Current UTC timestamp value in seconds used for hashing the `client_secret`
              required: true
              type: integer
              paramType: query
            - name: access_token
              description: Facebook API access token for user authentication
              required: true
              type: string
              paramType: form
        parameters_strategy:
            form: replace
        responseMessages:
            - code: 201
              message: User successfully created and authenticated
            - code: 200
              message: Matching user found and authenticated
            - code: 401
              message: Authentication failed
        """
        access_token = request.POST.get('access_token')
        if not access_token:
            raise exceptions.ValidationError('Facebook access_token is missing')

        self._get_client(request)

        try:
            # TODO: add appsecret_proof for better security once facebook-sdk supports it,
            # see https://github.com/mobolic/facebook-sdk/pull/243
            graph = facebook.GraphAPI(access_token, version=self.FACEBOOK_API_VERSION)
            user_info = graph.get_object('me', fields=self.FACEBOOK_USER_FIELDS)
        except facebook.GraphAPIError as exc:
            if exc.code in ('OAuthException', '102'):
                raise exceptions.AuthenticationFailed()
            else:
                logger.exception(exc.message)
                raise exceptions.ValidationError('Facebook access token error')

        user_info = self._map_user_info(user_info)
        try:
            user = User.objects.get_by_external_id(user_info['external_id'], user_info.get('email', None))
            serializer = self.get_serializer(user, data=user_info, partial=True)
            http_status = status.HTTP_200_OK
        except User.DoesNotExist:
            serializer = self.get_serializer(data=user_info)
            http_status = status.HTTP_201_CREATED
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return response.Response(serializer.data, status=http_status)

    def _map_user_info(self, user_info):
        data = {
            'external_id': user_info['id'],
            'first_name': user_info.get('first_name', ''),
            'middle_name': user_info.get('middle_name', ''),
            'last_name': user_info.get('last_name', '')
        }
        if user_info.get('email', None):
            data['email'] = user_info['email']
        return data


class ClaimListView(ClaimCreateMixin, ClientAuthMixin, generics.ListCreateAPIView):
    queryset = Claim.objects.authorized()
    serializer_class = ClaimSerializer
    permission_classes = (permissions.AllowAny,)
    filter_fields = ('status', 'crimetypes', 'city', 'created_at')

    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of all claims, optionally filtered by `status`, `crimetypes` and `city`.

        Doesn't need user authentication but requires providing client id and secret pair for an API client, which
        has a "can_list_all_claims" permission.
        ---
        parameters:
            - name: client_id
              description: ID of the API Client
              required: true
              type: string
              paramType: query
            - name: client_secret
              description: Secret of the API Client hashed with a timestamp as `SHA256(secret + timestamp)`
              required: true
              type: string
              paramType: query
            - name: timestamp
              description: Current UTC timestamp value in seconds used for hashing the `client_secret`
              required: true
              type: integer
              paramType: query
        """
        client = self._get_client(request)

        if not client.has_perm('can_list_all_claims'):
            raise exceptions.PermissionDenied()

        return super(ClaimListView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Creates an anonymous (unauthorized) claim.

        In order to be processed such claim requires authorization at some point.

        Doesn't need user authentication but requires providing client id and secret pair for an API client.
        ---
        parameters:
            - name: client_id
              description: ID of the API Client
              required: true
              type: string
              paramType: query
            - name: client_secret
              description: Secret of the API Client hashed with a timestamp as `SHA256(secret + timestamp)`
              required: true
              type: string
              paramType: query
            - name: timestamp
              description: Current UTC timestamp value in seconds used for hashing the `client_secret`
              required: true
              type: integer
              paramType: query
            - name: images
              required: true
              type: File
              paramType: form
        """
        self._get_client(request)
        return super(ClaimListView, self).post(request, *args, **kwargs)


class ClaimAuthorizeView(generics.GenericAPIView):
    queryset = Claim.objects.unauthorized()
    serializer_class = ClaimSerializer

    def post(self, request, *args, **kwargs):
        """
        Authorizes a given claim by a current user if it's not yet authorized.
        ---
        omit_parameters:
            - form
        """
        claim = self.get_object()
        claim.user = request.user
        claim.authorized_at = timezone.now()
        claim.save()

        serializer = self.get_serializer(claim)
        return response.Response(serializer.data)


class CurrentUserClaimViewSet(ClaimCreateMixin,
                              mixins.CreateModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    """
    Create, update, get and list operations over current user's claims.
    """
    serializer_class = ClaimSerializer
    filter_fields = ('status', 'crimetypes', 'city', 'created_at')

    def get_queryset(self):
        return self.request.user.claims.all()

    @detail_route(methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a claim provided by ID.

        Can only cancel enqueued claims. If a claim has moved further in status it's not possible to cancel anymore.
        Requires user authentication.
        ---
        omit_serializer: true
        """
        claim = self.get_object()
        if claim.is_cancelable():
            claim.cancel()
            return response.Response({'status': 'canceled'})
        else:
            raise exceptions.ValidationError('This claim can not be canceled')

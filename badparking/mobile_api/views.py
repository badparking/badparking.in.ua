from django.utils import timezone
from rest_framework import viewsets, permissions, response, generics, exceptions, mixins
from rest_framework.decorators import detail_route

from core.models import CrimeType, Claim
from profiles.serializers import UserSerializer
from .serializers import ClaimSerializer, CrimeTypeSerializer, UserCompleteSerializer
from .models import Client


class CrimeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve crime types.
    """
    queryset = CrimeType.objects.filter(enabled=True)
    serializer_class = CrimeTypeSerializer
    permission_classes = (permissions.AllowAny,)


class UserObjectMixin(object):
    def get_object(self):
        user = self.request.user
        self.check_object_permissions(self.request, user)

        return user


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


class ClaimCreateMixin:
    def perform_create(self, serializer):
        # Currently DRF doesn't seem to pass lists of files into the validated data, hence this explicit way
        image_files = []
        if self.request.FILES:
            image_files = self.request.FILES.getlist('images')
        serializer.save(image_files=image_files)


class ClaimListView(ClaimCreateMixin, generics.ListCreateAPIView):
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

    def _get_client(self, request):
        client_id = request.GET.get('client_id')
        client_secret = request.GET.get('client_secret')
        timestamp = request.GET.get('timestamp')
        if not client_id or not client_secret or not timestamp:
            raise exceptions.NotAuthenticated()

        try:
            client = Client.objects.get(id=client_id, is_active=True)
            client.verify_secret(client_secret, timestamp, raise_exception=True)
        except (Client.DoesNotExist, ValueError):
            raise exceptions.AuthenticationFailed()

        return client


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

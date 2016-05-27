from rest_framework import viewsets, permissions, views, response, generics, exceptions, mixins
from rest_framework.decorators import detail_route
from core.models import CrimeType, Claim
from profiles.serializers import UserSerializer
from .serializers import ClaimSerializer, CrimeTypeSerializer
from .models import Client


class CrimeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve crime types.
    """
    queryset = CrimeType.objects.filter(enabled=True)
    serializer_class = CrimeTypeSerializer
    permission_classes = (permissions.AllowAny,)


class CurrentUserView(views.APIView):

    def get(self, request):
        """
        Retrieve user associated with the current authenticated request.
        ---
        response_serializer: UserSerializer
        """
        serializer = UserSerializer(request.user)
        return response.Response(serializer.data)


class ClaimListView(generics.ListAPIView):
    queryset = Claim.objects.all()
    serializer_class = ClaimSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_fields = ('status', 'crimetypes', 'city')

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
              description: Secret of the API Client corresponding to ID
              required: true
              type: string
              paramType: query
        """
        client_id = request.GET.get('client_id')
        client_secret = request.GET.get('client_secret')
        if not client_id or not client_secret:
            raise exceptions.NotAuthenticated()

        try:
            client = Client.objects.get(id=client_id, secret=client_secret, is_active=True)
        except (Client.DoesNotExist, ValueError):
            raise exceptions.AuthenticationFailed()

        if not client.has_perm('can_list_all_claims'):
            raise exceptions.PermissionDenied()

        return super(ClaimListView, self).get(request, *args, **kwargs)


class CurrentUserClaimViewSet(mixins.CreateModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    """
    Create, update, get and list operations over current user's claims.
    """
    serializer_class = ClaimSerializer
    filter_fields = ('status', 'crimetypes', 'city')

    def get_queryset(self):
        return self.request.user.claims.all()

    def perform_create(self, serializer):
        # Currently DRF doesn't seem to pass lists of files into the validated data, hence this explicit way
        image_files = []
        if self.request.FILES:
            image_files = self.request.FILES.getlist('images')
        serializer.save(image_files=image_files)

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

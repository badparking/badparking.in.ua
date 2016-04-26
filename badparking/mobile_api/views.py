from rest_framework import viewsets, permissions, views, response

from core.models import CrimeType
from profiles.serializers import UserSerializer
from .serializers import CrimeTypeSerializer


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

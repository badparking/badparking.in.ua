from django.http import Http404
from rest_framework import viewsets, permissions, views, response, status
from core.models import CrimeType
from media.models import MediaFileModel
from .serializers import ClaimSerializer, CrimeTypeSerializer
from profiles.serializers import UserSerializer


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


class ClaimList(views.APIView):
    def post(self, request, format=None):
        serializer = ClaimSerializer(data=request.data, request=request)

        if serializer.is_valid():
            claim = serializer.save()

            if request.FILES:
                for img in request.FILES.getlist('images'):
                    image = MediaFileModel()
                    image.file.save(img.name, img)
                    image.save()
                    claim.images.add(image)

            types = request.data.getlist('types')
            if types:
                ct = CrimeType.objects.filter(id__in=types)
                claim.crimetypes.add(*ct)

            return response.Response(serializer.data, status=status.HTTP_201_CREATED)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

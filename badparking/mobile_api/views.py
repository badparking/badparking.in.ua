from django.http import Http404
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.models import Claim, CrimeType
from media.models import MediaFileModel
from .serializers import ClaimSerializer


class ClaimList(APIView):
    def get(self, request, format=None):
        claims = Claim.objects.all()
        serializer = ClaimSerializer(claims, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ClaimSerializer(data=request.data)

        if serializer.is_valid():
            claim = Claim(**serializer.data)
            # temporary solution until we'll have auth
            claim.user = request.user if request.user.id else User.objects.all()[0]
            claim.save()

            if (request.FILES):
                for img in request.FILES.getlist('images'):
                    image = MediaFileModel()
                    image.file.save(img.name, img)
                    image.save()
                    claim.images.add(image)

            types = request.data.getlist('types')
            if (types):
                ct = CrimeType.objects.filter(name__in = types)
                claim.crimetypes.add(*ct)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

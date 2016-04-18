from rest_framework import serializers, viewsets
from core.models import CrimeType, Claim


class CrimeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeType
        fields = ('name',)


class CrimeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CrimeType.objects.filter(enabled=True)
    serializer_class = CrimeTypeSerializer


class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = ('license_plates', 'longitude', 'latitude', 'city', 'address')

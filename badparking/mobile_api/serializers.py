from rest_framework import serializers
from core.models import CrimeType, Claim


class CrimeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeType
        fields = ('id', 'name',)


class ClaimSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return Claim(**validated_data)

    class Meta:
        model = Claim
        fields = ('license_plates', 'longitude', 'latitude', 'city', 'address')

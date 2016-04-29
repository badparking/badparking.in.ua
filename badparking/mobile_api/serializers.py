from rest_framework import serializers
from core.models import CrimeType, Claim
from django.contrib.auth import get_user_model

class CrimeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeType
        fields = ('id', 'name',)


class ClaimSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'request' arg up to the superclass
        request = kwargs.pop('request', None)
        # Instatiate the superclass normally
        super(serializers.ModelSerializer, self).__init__(*args, **kwargs)
        self.request = request

    def create(self, validated_data):
        claim = Claim(**validated_data)
        claim.user = self.request.user
        claim.save()
        return claim

    class Meta:
        model = Claim
        fields = ('license_plates', 'longitude', 'latitude', 'city', 'address')

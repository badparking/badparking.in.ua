from rest_framework import serializers
from core.models import CrimeType


class CrimeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeType
        fields = ('id', 'name',)

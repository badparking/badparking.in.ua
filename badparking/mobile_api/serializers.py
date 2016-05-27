from rest_framework import serializers
from core.models import CrimeType, Claim
from media.models import MediaFileModel
from profiles.serializers import UserSerializer


class CrimeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeType
        fields = ('id', 'name',)


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFileModel
        fields = ('file',)


class ClaimSerializer(serializers.ModelSerializer):
    images = MediaFileSerializer(many=True, read_only=True)
    user = UserSerializer(default=serializers.CurrentUserDefault(), read_only=True)

    class Meta:
        model = Claim
        fields = ('pk', 'license_plates', 'longitude', 'latitude', 'city', 'address', 'user', 'crimetypes', 'images',
                  'status', 'images')
        read_only_fields = ('status',)

    def create(self, validated_data):
        image_files = validated_data.pop('image_files', [])
        claim = super(ClaimSerializer, self).create(validated_data)
        for image_file in image_files:
            # TODO: file names should not be guessable, randomize them
            image = MediaFileModel.objects.create(file=image_file)
            claim.images.add(image)
        return claim

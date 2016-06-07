from rest_framework import serializers
from core.models import CrimeType, Claim, ClaimState
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


class ClaimStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimState
        fields = ('status', 'description', 'logged_at')


class ClaimSerializer(serializers.ModelSerializer):
    images = MediaFileSerializer(many=True, read_only=True)
    user = UserSerializer(default=serializers.CurrentUserDefault(), read_only=True)
    states = ClaimStateSerializer(many=True, read_only=True)

    class Meta:
        model = Claim
        fields = ('pk', 'license_plates', 'longitude', 'latitude', 'city', 'address', 'user', 'crimetypes', 'images',
                  'status', 'images', 'states', 'created_at', 'modified_at')
        read_only_fields = ('status', 'created_at', 'modified_at')

    def validate_user(self, value):
        if not value.is_complete():
            raise serializers.ValidationError('User profile is not complete')
        return value

    def create(self, validated_data):
        image_files = validated_data.pop('image_files', [])
        claim = super(ClaimSerializer, self).create(validated_data)
        for image_file in image_files:
            # TODO: file names should not be guessable, randomize them
            image = MediaFileModel.objects.create(file=image_file)
            claim.images.add(image)
        return claim


class UserCompleteSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        fields = ('first_name', 'middle_name', 'last_name', 'full_name', 'email', 'dob', 'inn',
                  'username', 'phone', 'is_complete')
        read_only_fields = ('first_name', 'middle_name', 'last_name', 'full_name', 'inn', 'username')
        extra_kwargs = {}

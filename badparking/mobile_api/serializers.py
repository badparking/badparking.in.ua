from django.utils import timezone
from rest_framework import serializers

from core.models import CrimeType, Claim, ClaimState
from media.models import MediaFileModel
from profiles.serializers import UserSerializer
from profiles.jwt import jwt_from_user


class CrimeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeType
        fields = ('id', 'name',)


class MediaFileSerializer(serializers.ModelSerializer):
    # Specifying this explicitly as DRF doesn't have a mapping for ImageKit, thus unaware it should grab the URL
    thumbnail = serializers.ImageField(read_only=True)

    class Meta:
        model = MediaFileModel
        fields = ('file', 'thumbnail', 'original_filename')
        read_only_fields = ('original_filename',)

    def create(self, validated_data):
        validated_data['original_filename'] = validated_data['file'].name
        return super(MediaFileSerializer, self).create(validated_data)


class ClaimStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimState
        fields = ('status', 'description', 'logged_at')


class ClaimSerializer(serializers.ModelSerializer):
    media = MediaFileSerializer(many=True, read_only=True)
    user = UserSerializer(default=serializers.CurrentUserDefault(), read_only=True)
    states = ClaimStateSerializer(many=True, read_only=True)

    class Meta:
        model = Claim
        fields = ('pk', 'license_plates', 'longitude', 'latitude', 'city', 'address', 'user', 'crimetypes', 'media',
                  'media_filenames', 'status', 'states', 'created_at', 'modified_at', 'authorized_at')
        read_only_fields = ('status', 'created_at', 'modified_at', 'authorized_at')

    def validate_user(self, value):
        if value and value.is_authenticated() and not value.is_complete():
            raise serializers.ValidationError('User profile is not complete')
        return value

    def create(self, validated_data):
        if 'user' in validated_data:
            if validated_data['user'].is_authenticated():
                validated_data['authorized_at'] = timezone.now()
            else:
                validated_data.pop('user')
        return super(ClaimSerializer, self).create(validated_data)


class ClaimReadSerializer(ClaimSerializer):
    crimetypes = CrimeTypeSerializer(many=True)


class UserCompleteSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        fields = ('first_name', 'middle_name', 'last_name', 'full_name', 'email', 'inn',
                  'username', 'phone', 'is_complete')
        read_only_fields = ('first_name', 'middle_name', 'last_name', 'full_name', 'inn', 'username')
        extra_kwargs = {}


class FacebookAuthUserSerializer(UserSerializer):
    token = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('token',)

    def get_token(self, obj):
        return jwt_from_user(obj)

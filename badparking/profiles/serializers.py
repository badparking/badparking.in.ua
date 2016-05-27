import re
import uuid

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    identity = serializers.CharField(read_only=True)
    # On the model this field is not required but when it's coming through deserializer we should enforce it
    passport = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ('identity', 'passport', 'first_name', 'middle_name', 'last_name', 'email', 'dob', 'inn',
                  'provider_type', 'username')
        extra_kwargs = {
            'provider_type': {'write_only': True},
            'username': {'write_only': True, 'required': False},
            'inn': {'write_only': True}
        }

    def validate_passport(self, value):
        if not re.match(r'^\w{2} \d{6}$', value):
            raise serializers.ValidationError('Passport value is invalid')
        return value

    def create(self, validated_data):
        # Generate and inject username and password because Django requires it
        validated_data['username'] = validated_data.get('inn', '') or validated_data['passport']
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(str(uuid.uuid4()))
        user.save()
        return user

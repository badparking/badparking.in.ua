import re
import uuid

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    identity = serializers.CharField(read_only=True)
    # On the model this field is not required but when it's coming through deserializer we should enforce it
    passport = serializers.CharField(required=True)

    class Meta:
        model = User
        exclude = ('password', 'groups', 'user_permissions', 'is_active', 'is_staff', 'is_superuser')
        read_only_fields = ('username',)

    def validate_passport(self, value):
        if not re.match(r'\w{2} \d{6}', value):
            raise serializers.ValidationError('Passport value is invalid')
        return value

    def create(self, validated_data):
        # Generate and inject username and password because Django requires it
        validated_data['username'] = validated_data.get('inn', '') or validated_data['passport']
        validated_data['password'] = str(uuid.uuid4())
        return super(UserSerializer, self).create(validated_data)

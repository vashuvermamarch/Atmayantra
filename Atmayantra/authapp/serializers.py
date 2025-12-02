from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'password',
            'user_type',
            'is_verified',
            'is_active',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'is_verified': {'read_only': True},
            'is_active': {'read_only': True},
        }

    def create(self, validated_data):
        # This will call our custom manager create_user
        user = User.objects.create_user(**validated_data)
        return user

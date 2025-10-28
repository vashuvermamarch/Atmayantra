from rest_framework import serializers
from .models import AdminUser
from django.contrib.auth.hashers import make_password

class AdminSignUpSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = AdminUser
        fields = ['contact_number', 'name', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data['password'] = make_password(validated_data['password'])
        return AdminUser.objects.create(**validated_data)


class AdminVerifyOtpSerializer(serializers.Serializer):
    contact_number = serializers.CharField()
    otp = serializers.CharField(max_length=6)

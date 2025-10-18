from rest_framework import serializers
from .models import DoctorPersonalDetails
import base64

class DoctorPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorPersonalDetails
        fields = '__all__'

class DoctorPersonalDetailsWriteSerializer(serializers.ModelSerializer):
    profile_photo_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = DoctorPersonalDetails
        fields = ['contact_number', 'full_name', 'specialization', 'experience', 'hospital', 'gender', 'email', 'address', 'profile_photo_file', 'profile_photo']
        extra_kwargs = {
            'profile_photo': {'read_only': True}
        }

    def create(self, validated_data):
        profile_photo_file = validated_data.pop('profile_photo_file', None)
        if profile_photo_file:
            encoded_string = base64.b64encode(profile_photo_file.read()).decode('utf-8')
            validated_data['profile_photo'] = encoded_string
        return super().create(validated_data)

    def update(self, instance, validated_data):
        profile_photo_file = validated_data.pop('profile_photo_file', None)
        if profile_photo_file:
            encoded_string = base64.b64encode(profile_photo_file.read()).decode('utf-8')
            validated_data['profile_photo'] = encoded_string
        return super().update(instance, validated_data)

    def validate_contact_number(self, value):
        # Strip whitespace from the contact number
        return value.strip()

from common.fields import Base64StringFileField
from rest_framework import serializers

from .models import DoctorPersonalDetails, DoctorProfilePhoto


class DoctorProfilePhotoSerializer(serializers.ModelSerializer):
    photo_data = Base64StringFileField(required=True)

    class Meta:
        model = DoctorProfilePhoto
        fields = ['photo_data']

class DoctorProfilePhotoWriteSerializer(serializers.Serializer):
    contact_number = serializers.CharField(max_length=15)
    photo_data = Base64StringFileField(required=True)


class DoctorPersonalDetailsWriteSerializer(serializers.ModelSerializer):
    profile_photo = Base64StringFileField(required=False, allow_null=True)

    class Meta:
        model = DoctorPersonalDetails
        fields = [
            'contact_number', 'full_name', 'date_of_birth', 'gender',
            'email', 'state', 'city', 'pincode', 'spoken_language',
            'profile_photo'
        ]

    def create(self, validated_data):
        profile_photo = validated_data.pop('profile_photo', None)
        # Use update_or_create to handle both creation and updates gracefully.
        doctor, created = DoctorPersonalDetails.objects.update_or_create(
            contact_number=validated_data['contact_number'],
            defaults=validated_data
        )
        if profile_photo:
            DoctorProfilePhoto.objects.update_or_create(
                doctor=doctor,
                defaults={'photo_data': profile_photo['content']}
            )
        return doctor

    def update(self, instance, validated_data):
        return self.create(validated_data) # Reuse create logic for simplicity

class DoctorPersonalDetailsSerializer(serializers.ModelSerializer):
    profile_photo = serializers.CharField(source='profile_photo_data.photo_data', read_only=True)

    class Meta:
        model = DoctorPersonalDetails
        fields = [
            'contact_number', 'full_name', 'date_of_birth', 'gender', 'email',
            'state', 'city', 'pincode', 'spoken_language', 'profile_photo'
        ]
        read_only_fields = fields

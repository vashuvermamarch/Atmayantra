from rest_framework import serializers
from .models import DoctorPersonalDetails, DoctorProfilePhoto
from common.fields import Base64StringFileField

class DoctorProfilePhotoSerializer(serializers.ModelSerializer):
    photo_data = Base64StringFileField(required=True)

    class Meta:
        model = DoctorProfilePhoto
        fields = ['photo_data']

class DoctorProfilePhotoWriteSerializer(serializers.Serializer):
    contact_number = serializers.CharField(max_length=15)
    photo_data = Base64StringFileField(required=True)


class DoctorPersonalDetailsWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = DoctorPersonalDetails
        fields = [
            'contact_number', 'full_name', 'date_of_birth', 'gender',
            'email', 'state', 'city', 'pincode', 'spoken_language'
        ]

    def create(self, validated_data):
        # Use update_or_create to handle both creation and updates gracefully.
        doctor, created = DoctorPersonalDetails.objects.update_or_create(
            contact_number=validated_data['contact_number'],
            defaults=validated_data
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

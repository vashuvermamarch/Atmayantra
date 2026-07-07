from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import TrainerPersonalDetails


class TrainerPersonalDetailSerializer(serializers.ModelSerializer):
    profile_photo = serializers.FileField(write_only=True, required=False, allow_null=True)
    profile_photo_url = serializers.SerializerMethodField()

    date_of_birth = serializers.DateField(
        input_formats=['%Y-%m-%d', '%d-%m-%Y'],
        required=False,
        allow_null=True
    )

    class Meta:
        model = TrainerPersonalDetails
        fields = [
            'contact_number',
            'full_name',
            'date_of_birth',
            'gender',
            'email',
            'state',
            'city',
            'pincode',
            'spoken_language',
            'profile_photo',
            'profile_photo_url',
            'profile_photo_mimetype'
        ]
        read_only_fields = ['profile_photo_url', 'profile_photo_mimetype']

    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            request = self.context.get('request')
            return reverse(
                'trainer-personal-detail-view-profile-photo',
                args=[obj.contact_number],
                request=request
            )
        return None

    def create(self, validated_data):
        uploaded_file = validated_data.pop('profile_photo', None)
        if uploaded_file:
            validated_data['profile_photo'] = uploaded_file.read()
            validated_data['profile_photo_mimetype'] = uploaded_file.content_type
        return super().create(validated_data)

    def update(self, instance, validated_data):
        uploaded_file = validated_data.pop('profile_photo', None)

        # Case 1 — user uploaded a new photo
        if uploaded_file and hasattr(uploaded_file, "read"):
            instance.profile_photo = uploaded_file.read()
            instance.profile_photo_mimetype = uploaded_file.content_type

        # Case 2 — user explicitly removed photo (null / empty string)
        elif 'profile_photo' in self.initial_data and uploaded_file in [None, '', 'null', 'None']:
            instance.profile_photo = None
            instance.profile_photo_mimetype = None

        # Case 3 — no change → keep old photo

        # Update all other text fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

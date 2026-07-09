from rest_framework import serializers

from .models import PhysioPersonalDetails


class PhysioPersonalDetailsSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = PhysioPersonalDetails
        exclude = ('profile_photo',)
        read_only_fields = ('user',)

    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri('/api/physio/personal-details/profile-photo/')
            return '/api/physio/personal-details/profile-photo/'
        return None

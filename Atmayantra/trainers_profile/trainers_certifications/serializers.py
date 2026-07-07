from rest_framework import serializers

from .models import TrainerCertification


class TrainerCertificationSerializer(serializers.ModelSerializer):
    yoga_certified = serializers.BooleanField(required=False)

    class Meta:
        model = TrainerCertification
        fields = [
            'trainer',
            'highest_degree',
            'specialization',
            'year_of_graduation',
            'work_experience',
            'yoga_certified',
            'registration_number',
            'certification_type',
            'issuing_authority',
        ]
        extra_kwargs = {
            'trainer': {'required': False},
        }

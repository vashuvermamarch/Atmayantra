import base64
from rest_framework import serializers
from .models import DoctorCertification


class DoctorCertificationSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DoctorCertification
        fields = (
            'doctor',
            'highest_degree',
            'specialization',
            'year_of_graduation',
            'registration_number',
            'work_experience',
            'yoga_certified',
            'certification_type',
            'issuing_authority',
            'graduation_certificate',
            'experience_letter',
            'resume_cv',
            'license_pdf',
        )

    def to_internal_value(self, data):
        """
        Handle both base64 strings and uploaded files for file fields.
        """
        mutable_data = data.copy()
        file_fields = ['graduation_certificate', 'experience_letter', 'resume_cv', 'license_pdf']

        for field in file_fields:
            file_obj = data.get(field)
            if file_obj:
                if hasattr(file_obj, 'read'):  # Handle file uploads
                    mutable_data[field] = base64.b64encode(file_obj.read()).decode('utf-8')
                elif isinstance(file_obj, (bytes, bytearray)):  # bytes data
                    mutable_data[field] = base64.b64encode(file_obj).decode('utf-8')
                elif isinstance(file_obj, str) and file_obj.strip().startswith('JVBERi0'):  # already base64
                    mutable_data[field] = file_obj
                else:
                    # Invalid type (e.g. plain string)
                    raise serializers.ValidationError({field: ["Not a valid file or base64 string."]})
            else:
                # No file provided — keep existing or null
                if self.instance:
                    mutable_data[field] = getattr(self.instance, field)

        return super().to_internal_value(mutable_data)

    def create(self, validated_data):
        return DoctorCertification.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

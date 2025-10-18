from rest_framework import serializers
from .models import DoctorCertification
from doctor_personal_details.models import DoctorPersonalDetails
import base64

class DoctorCertificationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorCertification
        exclude = ('graduation_certificate', 'experience_letter', 'resume_cv', 'license')

    def to_representation(self, instance):
        request = self.context.get('request')
        data = super().to_representation(instance)
        contact_number = instance.doctor.contact_number
        base_url = '/doctors_certifications'

        # Add URLs for file downloads
        if instance.graduation_certificate:
            data['graduation_certificate_url'] = request.build_absolute_uri(f'{base_url}/download/graduation-certificate/{contact_number}/')
            data['graduation_certificate_base64'] = instance.graduation_certificate
        if instance.experience_letter:
            data['experience_letter_url'] = request.build_absolute_uri(f'{base_url}/download/experience-letter/{contact_number}/')
            data['experience_letter_base64'] = instance.experience_letter
        if instance.resume_cv:
            data['resume_cv_url'] = request.build_absolute_uri(f'{base_url}/download/resume-cv/{contact_number}/')
            data['resume_cv_base64'] = instance.resume_cv
        if instance.license:
            data['license_url'] = request.build_absolute_uri(f'{base_url}/download/license/{contact_number}/')
            data['license_base64'] = instance.license
        
        # Ensure doctor contact number is in the representation
        data['doctor'] = contact_number

        return data

class DoctorCertificationWriteSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(write_only=True)
    graduation_certificate = serializers.FileField(write_only=True, required=False)
    experience_letter = serializers.FileField(write_only=True, required=False)
    resume_cv = serializers.FileField(write_only=True, required=False)
    license = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = DoctorCertification
        fields = (
            'doctor',
            'highest_degree',
            'year_of_graduation',
            'year_of_experience',
            'yoga_certified',
            'certification_type',
            'issuing_authority',
            'specialization',
            'license_number',
            'graduation_certificate',
            'experience_letter',
            'resume_cv',
            'license',
        )

    def validate(self, data):
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
        for field_name in ['graduation_certificate', 'experience_letter', 'resume_cv', 'license']:
            if field_name in data and data[field_name] is not None:
                uploaded_file = data[field_name]
                if uploaded_file.content_type not in allowed_types:
                    raise serializers.ValidationError(f"Invalid file type for {field_name}. Only PDF, JPG, and PNG are allowed.")
        return data

    def _encode_file(self, file):
        if file:
            return base64.b64encode(file.read()).decode('utf-8'), file.name
        return None, None

    def create(self, validated_data):
        contact_number = validated_data.pop('doctor')
        try:
            doctor_instance = DoctorPersonalDetails.objects.get(contact_number=contact_number)
        except DoctorPersonalDetails.DoesNotExist:
            raise serializers.ValidationError("Doctor with this contact number does not exist.")

        if DoctorCertification.objects.filter(doctor=doctor_instance).exists():
            raise serializers.ValidationError("A certification for this doctor already exists.")

        validated_data['doctor'] = doctor_instance

        validated_data['graduation_certificate'], validated_data['graduation_certificate_filename'] = self._encode_file(validated_data.pop('graduation_certificate', None))
        validated_data['experience_letter'], validated_data['experience_letter_filename'] = self._encode_file(validated_data.pop('experience_letter', None))
        validated_data['resume_cv'], validated_data['resume_cv_filename'] = self._encode_file(validated_data.pop('resume_cv', None))
        validated_data['license'], validated_data['license_filename'] = self._encode_file(validated_data.pop('license', None))

        certification = DoctorCertification.objects.create(**validated_data)
        return certification

    def update(self, instance, validated_data):
        if 'doctor' in validated_data:
            contact_number = validated_data.pop('doctor')
            try:
                doctor_instance = DoctorPersonalDetails.objects.get(contact_number=contact_number)
                instance.doctor = doctor_instance
            except DoctorPersonalDetails.DoesNotExist:
                raise serializers.ValidationError("Doctor with this contact number does not exist.")

        # Handle file updates
        if 'graduation_certificate' in validated_data:
            instance.graduation_certificate, instance.graduation_certificate_filename = self._encode_file(validated_data.pop('graduation_certificate', None))
        if 'experience_letter' in validated_data:
            instance.experience_letter, instance.experience_letter_filename = self._encode_file(validated_data.pop('experience_letter', None))
        if 'resume_cv' in validated_data:
            instance.resume_cv, instance.resume_cv_filename = self._encode_file(validated_data.pop('resume_cv', None))
        if 'license' in validated_data:
            instance.license, instance.license_filename = self._encode_file(validated_data.pop('license', None))

        # Update other fields
        instance.highest_degree = validated_data.get('highest_degree', instance.highest_degree)
        instance.year_of_graduation = validated_data.get('year_of_graduation', instance.year_of_graduation)
        instance.year_of_experience = validated_data.get('year_of_experience', instance.year_of_experience)
        instance.yoga_certified = validated_data.get('yoga_certified', instance.yoga_certified)
        instance.certification_type = validated_data.get('certification_type', instance.certification_type)
        instance.issuing_authority = validated_data.get('issuing_authority', instance.issuing_authority)
        instance.specialization = validated_data.get('specialization', instance.specialization)
        instance.license_number = validated_data.get('license_number', instance.license_number)

        instance.save()
        return instance

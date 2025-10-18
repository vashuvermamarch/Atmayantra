import base64
from rest_framework import serializers
from .models import DoctorDocument
from doctor_personal_details.models import DoctorPersonalDetails

class DoctorDocumentSerializer(serializers.ModelSerializer):
    doctor = serializers.SlugRelatedField(
        slug_field='contact_number',
        queryset=DoctorPersonalDetails.objects.all(),
        required=False
    )
    file = serializers.FileField(write_only=True, required=True)
    file_data = serializers.CharField(read_only=True)

    class Meta:
        model = DoctorDocument
        fields = (
            'id',
            'doctor',
            'doc_type',
            'side',
            'filename',
            'content_type',
            'file_data',
            'file',
        )
        read_only_fields = ('filename', 'content_type')

    def create(self, validated_data):
        uploaded_file = validated_data.pop('file')
        
        validated_data['filename'] = uploaded_file.name
        validated_data['content_type'] = uploaded_file.content_type
        validated_data['file_data'] = base64.b64encode(uploaded_file.read()).decode('utf-8')

        return DoctorDocument.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if 'file' in validated_data:
            uploaded_file = validated_data.pop('file')
            instance.filename = uploaded_file.name
            instance.content_type = uploaded_file.content_type
            instance.file_data = base64.b64encode(uploaded_file.read()).decode('utf-8')

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
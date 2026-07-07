from common.fields import Base64StringFileField
from rest_framework import serializers

from .models import DoctorDocument


class DoctorDocumentSerializer(serializers.ModelSerializer):
    file = Base64StringFileField(required=False, write_only=True)

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
        read_only_fields = ('id', 'doctor', 'filename', 'content_type', 'file_data')

    def create(self, validated_data):
        file_data_dict = validated_data.pop('file')
        validated_data['file_data'] = file_data_dict['content']
        validated_data['filename'] = file_data_dict['filename']
        validated_data['content_type'] = file_data_dict['content_type']
        return DoctorDocument.objects.create(**validated_data)

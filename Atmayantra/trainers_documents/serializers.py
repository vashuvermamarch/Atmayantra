from rest_framework import serializers

from .models import TrainerDocument


class TrainerDocumentSerializer(serializers.ModelSerializer):
    document_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = TrainerDocument
        fields = [
            'id', # Use the standard 'id' primary key
            'trainer',
            'document_type',
            'side',
            'document_file',
            'document_mimetype',
            'uploaded_at',
        ]
        read_only_fields = ['id', 'document_mimetype', 'uploaded_at']
        extra_kwargs = {
            'trainer': {'required': False}, # Not required during temporary creation
        }

    def create(self, validated_data):
        uploaded_file = validated_data.pop('document_file')
        validated_data['document_file'] = uploaded_file.read()
        validated_data['document_mimetype'] = uploaded_file.content_type
        return super().create(validated_data)

    def update(self, instance, validated_data):
        uploaded_file = validated_data.pop('document_file', None)

        if uploaded_file:
            instance.document_file = uploaded_file.read()
            instance.document_mimetype = uploaded_file.content_type

        instance.document_type = validated_data.get('document_type', instance.document_type)
        instance.side = validated_data.get('side', instance.side)

        instance.save()
        return instance

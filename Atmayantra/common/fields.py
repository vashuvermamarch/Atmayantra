import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers

class Base64FileField(serializers.FileField):
    """
    A Django REST Framework field for handling file uploads encoded as Base64.
    """
    def to_internal_value(self, data):
        if isinstance(data, str):
            # Check if the string is a base64 string
            if data.startswith('data:'):
                # Handle data URL format
                try:
                    format, datastr = data.split(';base64,')
                    ext = format.split('/')[-1]
                    filename = f"{uuid.uuid4()}.{ext}"
                    data = ContentFile(base64.b64decode(datastr), name=filename)
                except (ValueError, TypeError):
                    self.fail('invalid_file')
            else:
                # Handle raw base64 string
                try:
                    decoded_file = base64.b64decode(data)
                    # Generate a random filename with a default extension (e.g., .bin)
                    filename = f"{uuid.uuid4()}.bin"
                    data = ContentFile(decoded_file, name=filename)
                except (ValueError, TypeError):
                    self.fail('invalid_file')

        return super().to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None
        
        try:
            with value.open('rb') as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return None

class Base64StringFileField(serializers.Field):
    """
    A custom serializer field to handle file uploads and convert them to a dictionary
    containing the base64 string, filename, and content type.
    """
    def to_internal_value(self, data):
        import base64
        if isinstance(data, dict):
            return data

        # data is an InMemoryUploadedFile object
        try:
            content = base64.b64encode(data.read()).decode('utf-8')
            return {
                'content': content,
                'filename': data.name,
                'content_type': data.content_type
            }
        except Exception as e:
            raise serializers.ValidationError(f"Failed to encode file to base64: {e}")

    def to_representation(self, value):
        return value
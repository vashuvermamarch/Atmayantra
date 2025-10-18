
import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers

class Base64FileField(serializers.FileField):
    """
    A Django REST Framework field for handling file uploads encoded as Base64.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:'):
            # Base64 encoded file
            try:
                format, datastr = data.split(';base64,')
                ext = format.split('/')[-1]
                # Generate a random filename
                filename = f"{uuid.uuid4()}.{ext}"
                data = ContentFile(base64.b64decode(datastr), name=filename)
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

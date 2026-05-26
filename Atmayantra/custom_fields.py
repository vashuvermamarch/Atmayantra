import base64

from rest_framework import serializers


class Base64StringFileField(serializers.Field):
    """
    A custom serializer field to handle file uploads and convert them to a dictionary
    containing the base64 string, filename, and content type.
    """
    def to_internal_value(self, data):
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
        # This method is not used for writing, but for reading from the database.
        # The model stores the base64 string in the 'file_data' field.
        # We will just return the value as is.
        return value

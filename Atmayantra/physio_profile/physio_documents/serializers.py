from rest_framework import serializers
from .models import PhysioDocumentation

class PhysioDocumentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysioDocumentation
        fields = '__all__'
        read_only_fields = ('user',)

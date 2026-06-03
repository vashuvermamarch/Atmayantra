from rest_framework import serializers
from .models import PhysioPersonalDetails

class PhysioPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysioPersonalDetails
        fields = '__all__'
        read_only_fields = ('user',)

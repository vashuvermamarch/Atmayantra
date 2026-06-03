from rest_framework import serializers
from .models import PhysioCertification

class PhysioCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysioCertification
        fields = '__all__'
        read_only_fields = ('user',)

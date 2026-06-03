from rest_framework import serializers
from .models import PhysioBankDetails

class PhysioBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysioBankDetails
        fields = '__all__'
        read_only_fields = ('user',)

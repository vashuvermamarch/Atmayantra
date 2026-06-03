from rest_framework import serializers
from .models import TrainersPersonalDetails


class TrainerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainersPersonalDetails
        fields = ['id', 'full_name', 'email', 'phone', 'status', 'created_at']


class TrainerApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainersPersonalDetails
        fields = ['id', 'full_name', 'email', 'status', 'approved_by']
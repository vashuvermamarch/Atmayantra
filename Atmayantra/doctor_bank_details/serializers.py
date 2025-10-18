from rest_framework import serializers
from .models import DoctorBankDetails
from doctor_personal_details.models import DoctorPersonalDetails
import base64

class DoctorBankDetailsReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorBankDetails
        fields = (
            'doctor',
            'account_holder_name',
            'account_number',
            'ifsc_code',
            'upi_id',
            'account_type',
            'bank_qr_code',
        )

class DoctorBankDetailsWriteSerializer(serializers.ModelSerializer):
    doctor = serializers.SlugRelatedField(
        slug_field='contact_number',
        queryset=DoctorPersonalDetails.objects.all(),
        required=False
    )
    confirm_account_number = serializers.CharField(write_only=True, required=True)
    bank_qr_code_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = DoctorBankDetails
        fields = (
            'doctor',
            'account_holder_name',
            'account_number',
            'confirm_account_number',
            'ifsc_code',
            'upi_id',
            'account_type',
            'bank_qr_code',
            'bank_qr_code_file',
        )

        extra_kwargs = {
            'bank_qr_code': {'read_only': True},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['doctor'].read_only = True

    def validate(self, data):
        if data.get('account_number') != data.get('confirm_account_number'):
            raise serializers.ValidationError({"confirm_account_number": "Account numbers do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_account_number', None)
        qr_code_file = validated_data.pop('bank_qr_code_file', None)
        instance = super().create(validated_data)
        if qr_code_file:
            instance.bank_qr_code = base64.b64encode(qr_code_file.read()).decode('utf-8')
            instance.save()
        return instance

    def update(self, instance, validated_data):
        validated_data.pop('confirm_account_number', None)
        qr_code_file = validated_data.pop('bank_qr_code_file', None)
        instance = super().update(instance, validated_data)
        if qr_code_file:
            instance.bank_qr_code = base64.b64encode(qr_code_file.read()).decode('utf-8')
            instance.save()
        return instance

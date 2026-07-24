from rest_framework import serializers
from .models import DoctorBankDetails
from common.fields import Base64StringFileField

class DoctorBankDetailsReadSerializer(serializers.ModelSerializer):
    bank_qr_code = serializers.SerializerMethodField()
    bank_qr_code_view_url = serializers.SerializerMethodField()
    bank_qr_code_download_url = serializers.SerializerMethodField()

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
            'bank_qr_code_view_url',
            'bank_qr_code_download_url',
        )

    def get_bank_qr_code(self, obj):
        return obj.bank_qr_code

    def get_bank_qr_code_view_url(self, obj):
        if not obj.bank_qr_code:
            return None
        request = self.context.get('request')
        if not request:
            return None
        return request.build_absolute_uri(f"/doctor-bank/{obj.doctor.contact_number}/qr-code/view/")

    def get_bank_qr_code_download_url(self, obj):
        if not obj.bank_qr_code:
            return None
        request = self.context.get('request')
        if not request:
            return None
        return request.build_absolute_uri(f"/doctor-bank/{obj.doctor.contact_number}/qr-code/download/")


class DoctorBankDetailsWriteSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(required=True)
    confirm_account_number = serializers.CharField(write_only=True, required=True)
    bank_qr_code = Base64StringFileField(required=True)

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
        )

    def validate(self, data):
        if data.get('account_number') != data.get('confirm_account_number'):
            raise serializers.ValidationError({"confirm_account_number": "Account numbers do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_account_number', None)
        qr_code_data = validated_data.pop('bank_qr_code', None)
        if qr_code_data:
            validated_data['bank_qr_code'] = qr_code_data.get('content')
        return DoctorBankDetails.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('doctor', None)
        validated_data.pop('confirm_account_number', None)

        instance.account_holder_name = validated_data.get('account_holder_name', instance.account_holder_name)
        instance.account_number = validated_data.get('account_number', instance.account_number)
        instance.ifsc_code = validated_data.get('ifsc_code', instance.ifsc_code)
        instance.upi_id = validated_data.get('upi_id', instance.upi_id)
        instance.account_type = validated_data.get('account_type', instance.account_type)

        if 'bank_qr_code' in validated_data:
            qr_code_data = validated_data.pop('bank_qr_code')
            if qr_code_data:
                instance.bank_qr_code = qr_code_data.get('content')
                instance.bank_qr_code_content_type = qr_code_data.get('content_type')
            else:
                instance.bank_qr_code = None
        
        instance.save()
        return instance
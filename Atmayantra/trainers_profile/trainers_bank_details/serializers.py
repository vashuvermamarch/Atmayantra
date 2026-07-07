from rest_framework import serializers

from .models import TrainerBankDetails


class TrainerBankDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for TrainerBankDetails. Handles QR code upload and account number confirmation.
    """
    # Field for uploading the QR code file
    qr_code_upload = serializers.FileField(write_only=True, required=False, allow_null=True)

    # Field for confirming the account number, not stored in the database
    confirm_account_number = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = TrainerBankDetails
        fields = [
            'trainer',
            'account_holder_name',
            'account_number',
            'confirm_account_number',
            'ifsc_code',
            'upi_id',
            'account_type',
            'qr_code_upload',
        ]
        extra_kwargs = {
            'account_number': {'write_only': True}, # Hide account number from response
            'trainer': {'required': False}, # Not required during temporary creation
        }

    def validate(self, data):
        """
        Check that the account numbers match.
        """
        if data.get('account_number') != data.get('confirm_account_number'):
            raise serializers.ValidationError({"account_number": "Account numbers do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_account_number')
        qr_code_file = validated_data.pop('qr_code_upload', None)

        instance = super().create(validated_data)

        if qr_code_file:
            instance.qr_code = qr_code_file.read()
            instance.qr_code_mimetype = qr_code_file.content_type
            instance.save()

        return instance

    def update(self, instance, validated_data):
        validated_data.pop('confirm_account_number', None)
        qr_code_file = validated_data.pop('qr_code_upload', None)

        # Let DRF handle the update for all standard fields
        updated_instance = super().update(instance, validated_data)

        if qr_code_file:
            updated_instance.qr_code = qr_code_file.read()
            updated_instance.qr_code_mimetype = qr_code_file.content_type
            updated_instance.save()

        return updated_instance

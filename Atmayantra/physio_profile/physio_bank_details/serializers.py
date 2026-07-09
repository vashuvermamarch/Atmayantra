from rest_framework import serializers

from .models import PhysioBankDetails


class PhysioBankDetailsSerializer(serializers.ModelSerializer):
    upload_bank_qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = PhysioBankDetails
        exclude = ('upload_bank_qr_code',)
        read_only_fields = ('user',)

    def get_upload_bank_qr_code_url(self, obj):
        if obj.upload_bank_qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri('/api/physio/bank-details/qr-code/')
            return '/api/physio/bank-details/qr-code/'
        return None

from rest_framework import serializers

from .models import PhysioDocumentation


class PhysioDocumentationSerializer(serializers.ModelSerializer):
    aadhar_card_front_url = serializers.SerializerMethodField()
    aadhar_card_back_url = serializers.SerializerMethodField()
    pancard_url = serializers.SerializerMethodField()
    resume_cv_url = serializers.SerializerMethodField()
    certificate_url = serializers.SerializerMethodField()

    class Meta:
        model = PhysioDocumentation
        exclude = ('aadhar_card_front', 'aadhar_card_back', 'pancard', 'resume_cv', 'certificate')
        read_only_fields = ('user',)

    def get_aadhar_card_front_url(self, obj):
        return self.get_doc_url(obj, 'aadhar_card_front')

    def get_aadhar_card_back_url(self, obj):
        return self.get_doc_url(obj, 'aadhar_card_back')

    def get_pancard_url(self, obj):
        return self.get_doc_url(obj, 'pancard')

    def get_resume_cv_url(self, obj):
        return self.get_doc_url(obj, 'resume_cv')

    def get_certificate_url(self, obj):
        return self.get_doc_url(obj, 'certificate')

    def get_doc_url(self, obj, field_name):
        if getattr(obj, field_name):
            request = self.context.get('request')
            url_path = f"/api/physio/documents/{field_name}/"
            if request:
                return request.build_absolute_uri(url_path)
            return url_path
        return None

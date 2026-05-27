import base64
import logging
import mimetypes

from Atmayantra.utils import api_response
from common.permissions import IsAuthenticatedOrPostOnly
from django.core.cache import cache
from django.db import transaction
from django.http import Http404, HttpResponse
from doctor_certification.models import DoctorCertification
from doctor_documents.models import DoctorDocument, DoctorPersonalDetails
from doctor_personal_details.models import DoctorPersonalDetails
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser

from .models import DoctorBankDetails
from .serializers import DoctorBankDetailsReadSerializer, DoctorBankDetailsWriteSerializer

logger = logging.getLogger(__name__)
from doctor_personal_details.models import DoctorProfilePhoto


class DoctorBankDetailsViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser)
    queryset = DoctorBankDetails.objects.all()
    lookup_field = 'doctor__contact_number'
    lookup_url_kwarg = 'contact_number'
    permission_classes = [IsAuthenticatedOrPostOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DoctorBankDetailsWriteSerializer
        return DoctorBankDetailsReadSerializer

    def get_object(self):
        queryset = self.get_queryset()
        filter_kwargs = {self.lookup_field: self.kwargs.get(self.lookup_url_kwarg)}
        obj = queryset.filter(**filter_kwargs).first()
        if not obj:
            raise Http404
        self.check_object_permissions(self.request, obj)
        return obj

    def create(self, request, *args, **kwargs):
        temp_id = request.data.get('temp_id')
        if not temp_id:
            return api_response(False, "temp_id is required.", status_code=status.HTTP_400_BAD_REQUEST)

        # Resolve contact_number from session mapping
        session_key = f"doctor_onboarding_session_{temp_id}"
        contact_number = cache.get(session_key)

        if not contact_number:
            return api_response(False, "Invalid temp_id or session expired.", status_code=status.HTTP_400_BAD_REQUEST)

        # Retrieve data from cache
        personal_details_cache_key = f"doctor_personal_details_{contact_number}"
        personal_details_data = cache.get(personal_details_cache_key)
        if not personal_details_data:
            return api_response(False, "Personal details (step 1) are missing from cache.", status_code=status.HTTP_400_BAD_REQUEST)

        profile_photo_cache_key = f"doctor_profile_photo_{contact_number}"
        profile_photo_data = cache.get(profile_photo_cache_key)

        certification_cache_key = f"doctor_certification_{contact_number}"
        certification_data = cache.get(certification_cache_key)
        if not certification_data:
            return api_response(False, "Certification details (step 2) are missing from cache.", status_code=status.HTTP_400_BAD_REQUEST)

        documents_cache_key = f"doctor_documents_{contact_number}"
        documents_data = cache.get(documents_cache_key)
        if not documents_data:
            return api_response(False, "Document details (step 3) are missing from cache.", status_code=status.HTTP_400_BAD_REQUEST)

        # Prepare data for serializer (Inject doctor resolved from temp_id)
        serializer_data = request.data.copy()
        serializer_data['doctor'] = contact_number

        bank_details_serializer = self.get_serializer(data=serializer_data)
        bank_details_serializer.is_valid(raise_exception=True)
        bank_details_data = bank_details_serializer.validated_data

        try:
            with transaction.atomic():
                # Save personal details
                doctor = DoctorPersonalDetails.objects.create(**personal_details_data)

                # Save profile photo if provided
                if profile_photo_data:
                    DoctorProfilePhoto.objects.create(doctor=doctor, photo_data=profile_photo_data)

                # Save certification details
                certification_data.pop('doctor', None)
                DoctorCertification.objects.create(doctor=doctor, **certification_data)

                # Save documents
                for doc_data in documents_data:
                    file_dict = doc_data.get('file')
                    if file_dict:
                        DoctorDocument.objects.create(
                            doctor=doctor,
                            doc_type=doc_data.get('doc_type'),
                            side=doc_data.get('side'),
                            file_data=file_dict.get('content'),
                            filename=file_dict.get('filename'),
                            content_type=file_dict.get('content_type')
                        )
                    else:
                        DoctorDocument.objects.create(
                            doctor=doctor,
                            doc_type=doc_data.get('doc_type'),
                            side=doc_data.get('side')
                        )

                # Save bank details
                bank_details_data.pop('confirm_account_number', None)
                qr_code_data = bank_details_data.pop('bank_qr_code')
                bank_details_data['bank_qr_code'] = qr_code_data['content']
                bank_details_data['bank_qr_code_content_type'] = qr_code_data['content_type']
                bank_details_data['doctor'] = doctor
                DoctorBankDetails.objects.create(**bank_details_data)

            # Clear all cache including session mapping
            cache.delete(personal_details_cache_key)
            cache.delete(profile_photo_cache_key)
            cache.delete(certification_cache_key)
            cache.delete(documents_cache_key)
            cache.delete(session_key)

            return api_response(True, "Doctor registration complete! All details have been saved.", status_code=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error during final save: {e}", exc_info=True)
            return api_response(False, "An error occurred while saving the data.", str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """
        Handles PUT requests to update doctor bank details.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return api_response(True, "Bank details updated successfully.", serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Handles PATCH requests to partially update doctor bank details.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE requests to remove doctor bank details.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(True, "Bank details deleted successfully.", status_code=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='qr-code/view')
    def qr_code_view(self, request, contact_number=None):
        instance = self.get_object()
        if not instance.bank_qr_code:
            return api_response(False, "QR code not found.", status_code=status.HTTP_404_NOT_FOUND)

        try:
            try:
                # The bank_qr_code field might contain the base64 data URI scheme
                header, encoded = instance.bank_qr_code.split(',', 1)
                qr_code_data = base64.b64decode(encoded)
                content_type = header.split(':')[1].split(';')[0]
            except (ValueError, IndexError):
                # Fallback if the data URI scheme is not present
                qr_code_data = base64.b64decode(instance.bank_qr_code)
                # Attempt to guess content type, default to jpeg
                content_type = mimetypes.guess_type(f"qrcode.{instance.doctor.contact_number}")[0] or 'image/jpeg'

            return HttpResponse(qr_code_data, content_type=content_type)
        except Exception as e:
            logger.error(f"Error decoding QR code for viewing: {e}", exc_info=True)
            return api_response(False, "Error decoding QR code.", str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='qr-code/download')
    def qr_code_download(self, request, contact_number=None):
        instance = self.get_object()
        if not instance.bank_qr_code:
            return api_response(False, "QR code not found.", status_code=status.HTTP_404_NOT_FOUND)

        try:
            try:
                header, encoded = instance.bank_qr_code.split(',', 1)
                qr_code_data = base64.b64decode(encoded)
                content_type = header.split(':')[1].split(';')[0]
                extension = content_type.split('/')[-1]
            except (ValueError, IndexError):
                qr_code_data = base64.b64decode(instance.bank_qr_code)
                content_type = mimetypes.guess_type(f"qrcode.{instance.doctor.contact_number}")[0] or 'image/png'
                extension = mimetypes.guess_extension(content_type) or '.png'

            response = HttpResponse(qr_code_data, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="bank_qr_code_{instance.doctor.contact_number}.{extension}"'
            return response
        except Exception as e:
            logger.error(f"Error decoding QR code: {e}", exc_info=True)
            return api_response(False, "Error decoding QR code.", str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

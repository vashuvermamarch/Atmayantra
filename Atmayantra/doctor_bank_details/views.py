import base64
from datetime import datetime
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from doctor_certification.models import DoctorCertification
from doctor_documents.models import DoctorDocument
from doctor_personal_details.models import DoctorPersonalDetails
from .models import DoctorBankDetails
from .serializers import DoctorBankDetailsReadSerializer, DoctorBankDetailsWriteSerializer
from Atmayantra.Atmayantra.utils import api_response
import logging

logger = logging.getLogger(__name__)

class DoctorBankDetailsViewSet(viewsets.ModelViewSet):
    queryset = DoctorBankDetails.objects.all()
    lookup_field = 'doctor__contact_number'
    lookup_url_kwarg = 'contact_number'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DoctorBankDetailsWriteSerializer
        return DoctorBankDetailsReadSerializer

    def get_object(self):
        queryset = self.get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = queryset.filter(**filter_kwargs).first()
        if not obj:
            raise Http404
        self.check_object_permissions(self.request, obj)
        return obj

    def create(self, request, *args, **kwargs):
        logger.info("Starting final step of doctor registration.")
        registration_data = request.session.get('doctor_registration_data')
        if not registration_data or 'personal_details' not in registration_data or 'certification' not in registration_data:
            logger.warning("Attempted to create doctor bank details without completing previous steps.")
            return api_response(False, "Previous steps must be completed first.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            start_time = datetime.fromisoformat(registration_data['start_time'])
            if timezone.now() - start_time > timezone.timedelta(days=1):
                logger.warning("Doctor registration process expired.")
                del request.session['doctor_registration_data']
                return api_response(False, "The registration process has expired. Please start over.", status_code=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            logger.error("Could not parse start_time from session data.")
            return api_response(False, "Invalid session data. Please start over.", status_code=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data.pop('doctor', None)
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return api_response(False, "Invalid bank details provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        
        bank_details_data = serializer.validated_data

        try:
            with transaction.atomic():
                personal_details_data = registration_data['personal_details']
                doctor = DoctorPersonalDetails.objects.create(**personal_details_data)
                logger.info(f"Created doctor personal details for {doctor.contact_number}")

                certification_data = registration_data['certification']
                certification_data['doctor'] = doctor
                DoctorCertification.objects.create(**certification_data)
                logger.info(f"Created doctor certification for {doctor.contact_number}")

                documents_data = registration_data.get('documents', [])
                for doc_data in documents_data:
                    doc_data['doctor'] = doctor
                    DoctorDocument.objects.create(**doc_data)
                logger.info(f"Created {len(documents_data)} documents for {doctor.contact_number}")

                bank_details_data['doctor'] = doctor
                bank_details_data.pop('confirm_account_number', None)
                DoctorBankDetails.objects.create(**bank_details_data)
                logger.info(f"Created doctor bank details for {doctor.contact_number}")

        except Exception as e:
            logger.error(f"Error during doctor registration: {e}", exc_info=True)
            return api_response(False, f"An error occurred while saving data: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        del request.session['doctor_registration_data']
        logger.info(f"Successfully completed doctor registration for {doctor.contact_number}")
        return api_response(True, "Step 4 of 4: Doctor registration complete! All details saved.", status_code=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Bank details retrieved successfully.", serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return api_response(True, "Bank details updated successfully.", serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(True, "Bank details deleted successfully.", status_code=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def qr_code(self, request, contact_number=None):
        instance = self.get_object()
        if not instance.bank_qr_code:
            return api_response(False, "QR Code not found.", status_code=status.HTTP_404_NOT_FOUND)

        try:
            # The api_response helper handles FileResponse automatically
            decoded_file = base64.b64decode(instance.bank_qr_code)
            return api_response(file=decoded_file)
        except Exception as e:
            return api_response(False, f'Error processing QR code: {e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
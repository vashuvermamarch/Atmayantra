from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
import base64
from django.utils import timezone
from .models import DoctorCertification
from .serializers import DoctorCertificationReadSerializer, DoctorCertificationWriteSerializer
from Atmayantra.Atmayantra.utils import api_response

class DoctorCertificationViewSet(viewsets.ModelViewSet):
    queryset = DoctorCertification.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    lookup_field = 'contact_number'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DoctorCertificationWriteSerializer
        return DoctorCertificationReadSerializer

    def get_object(self):
        queryset = self.get_queryset()
        contact_number = self.kwargs.get(self.lookup_field)
        obj = get_object_or_404(queryset, doctor__contact_number=contact_number)
        self.check_object_permissions(self.request, obj)
        return obj

    def _get_file_response(self, file_content):
        if not file_content:
            return api_response(False, "File not found.", status_code=status.HTTP_404_NOT_FOUND)
        
        try:
            decoded_file = base64.b64decode(file_content)
            return api_response(file=decoded_file)
        except Exception as e:
            return api_response(False, f'Error processing file: {e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        registration_data = request.session.get('doctor_registration_data')
        if not registration_data or 'personal_details' not in registration_data:
            return api_response(False, "Step 1 (personal details) must be completed first.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            start_time = timezone.datetime.fromisoformat(registration_data['start_time'])
            if timezone.now() - start_time > timezone.timedelta(days=1):
                del request.session['doctor_registration_data']
                return api_response(False, "The registration process has expired. Please start over.", status_code=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
             return api_response(False, "Invalid session data. Please start over.", status_code=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data

        def _encode_file(file):
            if file:
                return {"name": file.name, "content": base64.b64encode(file.read()).decode('utf-8')}
            return None

        validated_data['graduation_certificate'] = _encode_file(validated_data.pop('graduation_certificate', None))
        validated_data['experience_letter'] = _encode_file(validated_data.pop('experience_letter', None))
        validated_data['resume_cv'] = _encode_file(validated_data.pop('resume_cv', None))
        validated_data['license'] = _encode_file(validated_data.pop('license', None))

        registration_data['certification'] = validated_data
        request.session['doctor_registration_data'] = registration_data
        request.session.modified = True

        return api_response(True, "Step 2 of 4 complete: Certification details received. Proceed to document submission.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = DoctorCertificationReadSerializer(instance, context={'request': request})
        return api_response(True, "Certification details updated successfully.", read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(True, "Doctor certification successfully deleted.", status_code=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def download_graduation_certificate(self, request, contact_number=None):
        certification = self.get_object()
        return self._get_file_response(certification.graduation_certificate)

    @action(detail=True, methods=['get'])
    def download_experience_letter(self, request, contact_number=None):
        certification = self.get_object()
        return self._get_file_response(certification.experience_letter)

    @action(detail=True, methods=['get'])
    def download_resume_cv(self, request, contact_number=None):
        certification = self.get_object()
        return self._get_file_response(certification.resume_cv)

    @action(detail=True, methods=['get'])
    def download_license(self, request, contact_number=None):
        certification = self.get_object()
        return self._get_file_response(certification.license)
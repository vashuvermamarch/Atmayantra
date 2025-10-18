from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import Http404
import base64
from django.utils import timezone
from datetime import datetime
from .models import DoctorDocument
from .serializers import DoctorDocumentSerializer
from Atmayantra.Atmayantra.utils import api_response

class DoctorDocumentViewSet(viewsets.ModelViewSet):
    queryset = DoctorDocument.objects.all()
    serializer_class = DoctorDocumentSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        registration_data = request.session.get('doctor_registration_data')
        if not registration_data or 'personal_details' not in registration_data:
            return api_response(False, "Step 1 (personal details) must be completed first.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            start_time = datetime.fromisoformat(registration_data['start_time'])
            if timezone.now() - start_time > timezone.timedelta(days=1):
                del request.session['doctor_registration_data']
                return api_response(False, "The registration process has expired. Please start over.", status_code=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return api_response(False, "Invalid session data. Please start over.", status_code=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data.pop('doctor', None)
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data

        uploaded_file = validated_data.pop('file')
        file_data = {
            'name': uploaded_file.name,
            'content_type': uploaded_file.content_type,
            'content': base64.b64encode(uploaded_file.read()).decode('utf-8')
        }
        validated_data['file'] = file_data
        
        for key, value in validated_data.items():
            if hasattr(value, 'pk'):
                validated_data[key] = value.pk

        if 'documents' not in registration_data:
            registration_data['documents'] = []
        registration_data['documents'].append(validated_data)
        request.session['doctor_registration_data'] = registration_data
        request.session.modified = True

        return api_response(True, "Step 3 of 4: Document added. Add more or proceed to bank details.")

    def list(self, request, *args, **kwargs):
        contact_number = self.kwargs.get('contact_number')
        queryset = self.get_queryset().filter(doctor__contact_number=contact_number)
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Documents retrieved successfully.", serializer.data)

    def get_object(self):
        queryset = self.get_queryset()
        try:
            obj = queryset.get(
                doctor__contact_number=self.kwargs.get('contact_number'),
                pk=self.kwargs.get('pk')
            )
            self.check_object_permissions(self.request, obj)
            return obj
        except DoctorDocument.DoesNotExist:
            raise Http404(f"Document with id {self.kwargs.get('pk')} not found for doctor {self.kwargs.get('contact_number')}.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(True, "Document deleted successfully.", status_code=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def file(self, request, contact_number=None, pk=None):
        doc = self.get_object()
        try:
            decoded_file = base64.b64decode(doc.file_data)
            return api_response(file=decoded_file)
        except Exception as e:
            return api_response(False, f'Error processing file: {e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework import viewsets, status
from rest_framework.decorators import action
from .models import DoctorPersonalDetails
from .serializers import DoctorPersonalDetailsSerializer, DoctorPersonalDetailsWriteSerializer
from rest_framework.parsers import MultiPartParser, FormParser
import base64
from django.utils import timezone
from Atmayantra.utils import api_response

class DoctorPersonalDetailsViewSet(viewsets.ModelViewSet):
    queryset = DoctorPersonalDetails.objects.all()
    lookup_field = 'contact_number'
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DoctorPersonalDetailsWriteSerializer
        return DoctorPersonalDetailsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data

        profile_photo_file = validated_data.pop('profile_photo', None)
        encoded_photo = None
        if profile_photo_file:
            encoded_photo = base64.b64encode(profile_photo_file.read()).decode('utf-8')

        for key, value in validated_data.items():
            if hasattr(value, 'pk'):
                validated_data[key] = value.pk

        validated_data['profile_photo'] = encoded_photo

        request.session['doctor_registration_data'] = {
            'personal_details': validated_data,
            'start_time': timezone.now().isoformat()
        }

        return api_response(True, "Step 1 of 4 complete: Personal details received. Proceed to certification details.", validated_data)

    @action(detail=False, methods=['get'], url_path='get-all-doctors')
    def get_all_doctors(self, request):
        queryset = self.get_queryset()
        serializer = DoctorPersonalDetailsSerializer(queryset, many=True)
        return api_response(True, "All doctors retrieved successfully.", serializer.data)

    @action(detail=True, methods=['get'])
    def photo(self, request, contact_number=None):
        doctor = self.get_object()
        if not doctor.profile_photo:
            return api_response(False, "Photo not found.", status_code=status.HTTP_404_NOT_FOUND)

        try:
            decoded_file = base64.b64decode(doctor.profile_photo)
            return api_response(file=decoded_file)
        except Exception as e:
            return api_response(False, "Error decoding photo.", str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = DoctorPersonalDetailsSerializer(instance)
        return api_response(True, "Personal details updated successfully.", read_serializer.data)
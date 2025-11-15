import base64
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache
from .models import DoctorCertification
from .serializers import DoctorCertificationSerializer
from doctor_personal_details.models import DoctorPersonalDetails
from common.permissions import IsAuthenticatedOrPostOnly


class DoctorCertificationView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    CACHE_TIMEOUT = 86400  # 24 hours
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrPostOnly]

    def get_object(self, contact_number):
        try:
            doctor = DoctorPersonalDetails.objects.get(contact_number=contact_number)
            return DoctorCertification.objects.get(doctor=doctor)
        except (DoctorPersonalDetails.DoesNotExist, DoctorCertification.DoesNotExist):
            return None

    def get(self, request, contact_number):
        certification = self.get_object(contact_number)
        if not certification:
            return Response({"success": False, "message": "Certification not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = DoctorCertificationSerializer(certification)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        contact_number = request.data.get('doctor')

        # Check if personal details from step 1 are in the cache
        personal_details_cache_key = f"doctor_personal_details_{contact_number}"
        if not cache.get(personal_details_cache_key):
            return Response({
                "success": False, 
                "message": "Personal details not found in cache. Please complete step 1 first."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = DoctorCertificationSerializer(data=request.data)
        if serializer.is_valid():
            # Save to cache instead of database
            certification_cache_key = f"doctor_certification_{contact_number}"
            cache.set(certification_cache_key, serializer.validated_data, timeout=self.CACHE_TIMEOUT)

            return Response({
                "success": True,
                "message": "Step 2 of 4: Certification details saved temporarily."
            }, status=status.HTTP_200_OK)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, contact_number):
        certification = self.get_object(contact_number)
        if not certification:
            return Response({"success": False, "message": "Certification not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorCertificationSerializer(certification, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Certification updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, contact_number):
        certification = self.get_object(contact_number)
        if not certification:
            return Response({"success": False, "message": "Certification not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorCertificationSerializer(certification, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Certification partially updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, contact_number):
        certification = self.get_object(contact_number)
        if not certification:
            return Response({"success": False, "message": "Certification not found."}, status=status.HTTP_404_NOT_FOUND)
        certification.delete()
        return Response({"success": True, "message": "Certification deleted successfully."}, status=status.HTTP_200_OK)


# ---------- FILE DOWNLOAD VIEWS ----------
class BaseFileDownloadView(APIView):
    field_name = None
    filename = None

    def get(self, request, contact_number):
        try:
            doctor = DoctorPersonalDetails.objects.get(contact_number=contact_number)
            certification = DoctorCertification.objects.get(doctor=doctor)
            file_data = getattr(certification, self.field_name)
            if not file_data:
                return Response({"success": False, "message": f"{self.field_name} not found."}, status=status.HTTP_404_NOT_FOUND)
            pdf_data = base64.b64decode(file_data)
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{self.filename}"'
            return response
        except (DoctorPersonalDetails.DoesNotExist, DoctorCertification.DoesNotExist):
            return Response({"success": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)


class GraduationCertificateDownloadView(BaseFileDownloadView):
    field_name = 'graduation_certificate'
    filename = 'graduation_certificate.pdf'


class ExperienceLetterDownloadView(BaseFileDownloadView):
    field_name = 'experience_letter'
    filename = 'experience_letter.pdf'


class ResumeCvDownloadView(BaseFileDownloadView):
    field_name = 'resume_cv'
    filename = 'resume_cv.pdf'


class LicenseDownloadView(BaseFileDownloadView):
    field_name = 'license_pdf'
    filename = 'license.pdf'

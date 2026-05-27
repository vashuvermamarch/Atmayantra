import base64
import mimetypes
import uuid

from Atmayantra.utils import api_response
from common.permissions import IsAuthenticatedOrPostOnly
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .models import DoctorPersonalDetails, DoctorProfilePhoto
from .serializers import (
    DoctorPersonalDetailsSerializer,
    DoctorPersonalDetailsWriteSerializer,
    DoctorProfilePhotoWriteSerializer,
)

CACHE_TIMEOUT = 86400  # 24 hours

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser


class DoctorPersonalDetailsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrPostOnly]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    """
    API View for managing Doctor Personal Details (including profile photo).
    """

    def post(self, request):
        """
        Creates doctor personal details and caches profile photo.
        """
        serializer = DoctorPersonalDetailsWriteSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            contact_number = validated_data.get('contact_number')
            if not contact_number:
                return api_response(False, "Contact number is required.", status_code=status.HTTP_400_BAD_REQUEST)

            profile_photo = validated_data.pop('profile_photo', None)

            # Save to cache instead of database
            cache_key = f"doctor_personal_details_{contact_number}"
            cache.set(cache_key, validated_data, timeout=CACHE_TIMEOUT)

            # Cache profile photo if uploaded
            if profile_photo:
                photo_cache_key = f"doctor_profile_photo_{contact_number}"
                cache.set(photo_cache_key, profile_photo['content'], timeout=CACHE_TIMEOUT)

            # Create a Session Mapping for the Frontend
            temp_id = uuid.uuid4().hex
            session_key = f"doctor_onboarding_session_{temp_id}"
            cache.set(session_key, contact_number, timeout=CACHE_TIMEOUT)

            return api_response(
                success=True,
                message="Step 1 of 4: Personal details saved temporarily.",
                data={"temp_id": temp_id},
                status_code=status.HTTP_200_OK
            )
        return api_response(
            success=False,
            message="Invalid data provided.",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request, contact_number=None):
        """
        Retrieves doctor personal details.
        """
        if contact_number:
            # Retrieve single doctor
            try:
                doctor = DoctorPersonalDetails.objects.get(pk=contact_number)
                serializer = DoctorPersonalDetailsSerializer(doctor)
                return api_response(
                    success=True,
                    message="Personal details retrieved from database.",
                    data=serializer.data,
                    status_code=status.HTTP_200_OK
                )
            except DoctorPersonalDetails.DoesNotExist:
                return api_response(
                    success=False,
                    message="Doctor not found.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        else:
            # Retrieve all doctors from the database
            doctors = DoctorPersonalDetails.objects.all()
            serializer = DoctorPersonalDetailsSerializer(doctors, many=True)
            return api_response(
                success=True,
                message="All doctor personal details retrieved successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

    def put(self, request, contact_number):
        """
        Updates a doctor's full personal details in the database.
        """
        try:
            doctor = DoctorPersonalDetails.objects.get(pk=contact_number)
        except DoctorPersonalDetails.DoesNotExist:
            return api_response(
                success=False,
                message="Doctor not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = DoctorPersonalDetailsWriteSerializer(doctor, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(
                success=True,
                message="Personal details updated successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
        return api_response(
            success=False,
            message="Invalid data provided.",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, contact_number):
        """
        Partially updates a doctor's personal details in the database.
        """
        try:
            doctor = DoctorPersonalDetails.objects.get(pk=contact_number)
        except DoctorPersonalDetails.DoesNotExist:
            return api_response(
                success=False,
                message="Doctor not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = DoctorPersonalDetailsWriteSerializer(doctor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(
                success=True,
                message="Personal details updated successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
        return api_response(
            success=False,
            message="Invalid data provided.",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


    def delete(self, request, contact_number):
        """Deletes a doctor's details from the database."""
        # Delete from database
        try:
            doctor = DoctorPersonalDetails.objects.get(pk=contact_number)
            doctor.delete()
            return api_response(
                success=True,
                message="Doctor details successfully deleted from cache and database.",
                status_code=status.HTTP_200_OK
            )
        except DoctorPersonalDetails.DoesNotExist:
            return api_response(
                success=False,
                message="Doctor not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

class DoctorProfilePhotoView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrPostOnly]
    """
    API View for managing a doctor's profile photo.
    """

    def post(self, request):
        """
        Creates or updates a doctor's profile photo.
        Expects 'contact_number' and 'photo_data' in the payload.
        """
        serializer = DoctorProfilePhotoWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        contact_number = serializer.validated_data['contact_number']
        photo_data = serializer.validated_data['photo_data']['content']

        # Save photo data to cache
        photo_cache_key = f"doctor_profile_photo_{contact_number}"
        cache.set(photo_cache_key, photo_data, timeout=CACHE_TIMEOUT)

        return api_response(
            success=True,
            message="Profile photo saved temporarily.",
            status_code=status.HTTP_200_OK
        )

    def put(self, request, contact_number=None):
        """
        Updates a doctor's profile photo using contact_number from the URL.
        """
        if not contact_number:
            return api_response(False, "Contact number must be provided in the URL.", status_code=status.HTTP_400_BAD_REQUEST)

        # Add contact_number to the request data for the serializer
        request.data['contact_number'] = contact_number
        return self.post(request)

    def delete(self, request):
        """
        Deletes a doctor's profile photo.
        Expects 'contact_number' in the payload.
        """
        contact_number = request.data.get('contact_number')
        if not contact_number:
            return api_response(False, "Contact number is required.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            photo = DoctorProfilePhoto.objects.get(pk=contact_number)
            photo.delete()
            return api_response(
                success=True,
                message="Profile photo deleted successfully.",
                status_code=status.HTTP_200_OK
            )
        except DoctorProfilePhoto.DoesNotExist:
            return api_response(
                success=False,
                message="Profile photo not found for this doctor.",
                status_code=status.HTTP_404_NOT_FOUND
            )


class ProfilePhotoViewerView(APIView):
    """
    API View for displaying a doctor's profile photo.
    """
    def get(self, request, contact_number):
        # 1. Check cache first for temporary photo
        photo_cache_key = f"doctor_profile_photo_{contact_number}"
        cached_photo_data = cache.get(photo_cache_key)

        photo_data_b64 = cached_photo_data

        # 2. If not in cache, check the database for permanent photo
        if not photo_data_b64:
            try:
                photo_obj = DoctorProfilePhoto.objects.get(pk=contact_number)
                photo_data_b64 = photo_obj.photo_data
            except DoctorProfilePhoto.DoesNotExist:
                pass # It's okay if it's not in the DB yet

        if not photo_data_b64:
            return api_response(success=False, message="Profile photo not found for this doctor.", status_code=status.HTTP_404_NOT_FOUND)

        # 3. Decode and serve the image
        try:
            if ',' in photo_data_b64:
                header, encoded = photo_data_b64.split(',', 1)
                image_data = base64.b64decode(encoded)
                content_type = header.split(':')[1].split(';')[0]
            else:
                image_data = base64.b64decode(photo_data_b64)
                content_type = mimetypes.guess_type(f"photo.{contact_number}")[0] or 'image/jpeg'
            return HttpResponse(image_data, content_type=content_type)
        except Exception as e:
            return api_response(success=False, message="Error decoding image.", data={'detail': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DoctorProfilePhotoDownloadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    """
    API View for downloading a doctor's profile photo.
    """
    def get(self, request, contact_number):
        try:
            photo = DoctorProfilePhoto.objects.get(pk=contact_number)
            if not photo.photo_data:
                return api_response(success=False, message="No profile photo found.", status_code=status.HTTP_404_NOT_FOUND)

            try:
                header, encoded = photo.photo_data.split(',', 1)
                image_data = base64.b64decode(encoded)
                content_type = header.split(':')[1].split(';')[0]
                extension = content_type.split('/')[-1]
                if extension and not extension.startswith('.'):
                    extension = f".{extension}"
            except (ValueError, IndexError):
                image_data = base64.b64decode(photo.photo_data)
                content_type = mimetypes.guess_type(f"photo.{contact_number}")[0] or 'image/jpeg'
                extension = mimetypes.guess_extension(content_type) or '.jpg'

            response = HttpResponse(image_data, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="profile_{contact_number}{extension}"'
            return response

        except DoctorProfilePhoto.DoesNotExist:
            return api_response(success=False, message="Profile photo not found for this doctor.", status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return api_response(success=False, message="Error processing image for download.", data={'detail': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

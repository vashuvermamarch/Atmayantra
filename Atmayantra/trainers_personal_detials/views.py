import base64
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from datetime import datetime

from .models import TrainerPersonalDetails
from .serializers import TrainerPersonalDetailSerializer

from rest_framework_simplejwt.authentication import JWTAuthentication
from authapp.decorators import login_required
from rest_framework.permissions import IsAuthenticated, AllowAny

from Atmayantra.utils import api_response   # ADDED

CACHE_TTL = 60 * 60 * 24  # 24 hours


def personal_key(cn):
    return f"trainer_personal_details_{cn}"


def normalize_date(date_str):
    if not date_str:
        return None

    formats = ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]

    for f in formats:
        try:
            return datetime.strptime(date_str, f).date()
        except:
            pass

    raise ValueError("Invalid date format. Use DD-MM-YYYY or YYYY-MM-DD.")


class TrainerPersonalDetailViewSet(viewsets.ModelViewSet):
    serializer_class = TrainerPersonalDetailSerializer
    queryset = TrainerPersonalDetails.objects.all()

    lookup_field = 'contact_number'
    lookup_url_kwarg = 'contact_number'

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.action in ["create", "view_profile_photo"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    # ----------------------------------------------------------
    # STEP 1: TEMPORARY PERSONAL DETAILS
    # ----------------------------------------------------------
    def create(self, request, *args, **kwargs):
        contact = request.data.get("contact_number")
        if not contact:
            return api_response(False, "contact_number is required", status_code=400)

        if not TrainerPersonalDetails.objects.filter(contact_number=contact).exists():

            try:
                dob = normalize_date(request.data.get("date_of_birth"))
            except ValueError as e:
                return api_response(False, str(e), status_code=400)

            temp = {
                "contact_number": contact,
                "full_name": request.data.get("full_name"),
                "date_of_birth": str(dob) if dob else None,
                "gender": request.data.get("gender"),
                "email": request.data.get("email"),
                "state": request.data.get("state"),
                "city": request.data.get("city"),
                "pincode": request.data.get("pincode"),
                "spoken_language": request.data.get("spoken_language"),
            }

            # File to base64
            file = request.FILES.get("profile_photo")
            if file:
                temp["profile_photo"] = base64.b64encode(file.read()).decode()
                temp["profile_photo_mimetype"] = file.content_type

            cache.set(personal_key(contact), temp, CACHE_TTL)

            return api_response(
                True,
                "Step 1 of 4: Personal details saved temporarily.",
                {"temporary_data": temp},
                status_code=200
            )

        return super().create(request, *args, **kwargs)

    # ----------------------------------------------------------
    # RETRIEVE
    # ----------------------------------------------------------
    @login_required
    def retrieve(self, request, contact_number=None):

        try:
            trainer = self.get_object()
            serializer = self.get_serializer(trainer)
            return api_response(True, "Permanent trainer data", serializer.data)
        except:
            pass

        # Temporary fallback
        temp = cache.get(personal_key(contact_number))
        if temp:
            return api_response(True, "Temporary trainer data", temp)

        return api_response(False, "Trainer not found.", status_code=404)

    # ----------------------------------------------------------
    # VIEW PHOTO → RETURN BASE64 JSON
    # ----------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='view/profile-photo')
    def view_profile_photo(self, request, contact_number=None):

        try:
            trainer = self.get_object()
            if trainer.profile_photo:
                photo_b64 = base64.b64encode(trainer.profile_photo).decode()
                return api_response(
                    True,
                    "Profile photo retrieved.",
                    {
                        "photo": photo_b64,
                        "mimetype": trainer.profile_photo_mimetype or "image/jpeg"
                    }
                )
        except:
            pass

        temp = cache.get(personal_key(contact_number))
        if temp and temp.get("profile_photo"):
            return api_response(
                True,
                "Temporary profile photo retrieved.",
                {
                    "photo": temp["profile_photo"],
                    "mimetype": temp.get("profile_photo_mimetype") or "image/jpeg"
                }
            )

        return api_response(False, "Profile photo not found.", status_code=404)

    # ----------------------------------------------------------
    # DOWNLOAD PHOTO → RETURN BASE64 JSON
    # ----------------------------------------------------------
    @login_required
    @action(detail=True, methods=['get'], url_path='download/profile-photo')
    def download_profile_photo(self, request, contact_number=None):

        trainer = self.get_object()
        if trainer.profile_photo:
            photo_b64 = base64.b64encode(trainer.profile_photo).decode()
            return api_response(
                True,
                "Profile photo download ready.",
                {
                    "filename": "profile_photo.jpg",
                    "file": photo_b64
                }
            )

        temp = cache.get(personal_key(contact_number))
        if temp and temp.get("profile_photo"):
            return api_response(
                True,
                "Temporary profile photo download ready.",
                {
                    "filename": "profile_photo_temp.jpg",
                    "file": temp["profile_photo"]
                }
            )

        return api_response(False, "Profile photo not found.", status_code=404)

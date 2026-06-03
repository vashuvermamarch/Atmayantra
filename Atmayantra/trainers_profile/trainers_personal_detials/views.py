from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
# Code add with me
from authapp.authentication import SoftJWTAuthentication
#======================

from datetime import datetime

from .models import TrainerPersonalDetails
from .serializers import TrainerPersonalDetailSerializer
from authapp.decorators import login_required
from Atmayantra.utils import api_response


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

    lookup_field = "contact_number"
    # Code add with me
    # SoftJWTAuthentication: inactive user token pe 401 nahi aayega
    authentication_classes = [SoftJWTAuthentication]
    #======================

    # Permissions
    def get_permissions(self):
        if self.action in ["create", "view_profile_photo"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    # ----------------------------------------------------------
    # STEP 1 — TEMPORARY PERSONAL DETAILS (NO BASE64)
    # ----------------------------------------------------------
    def create(self, request, *args, **kwargs):
        contact = request.data.get("contact_number")
        if not contact:
            return api_response(False, "contact_number is required", status_code=400)

        # If trainer does NOT exist → TEMP SAVE
        if not TrainerPersonalDetails.objects.filter(contact_number=contact).exists():

            try:
                dob = normalize_date(request.data.get("date_of_birth"))
            except ValueError as e:
                return api_response(False, str(e), status_code=400)

            temp = {
                "contact_number": contact,
                "full_name": request.data.get("full_name"),
                "date_of_birth": dob,
                "gender": request.data.get("gender"),
                "email": request.data.get("email"),
                "state": request.data.get("state"),
                "city": request.data.get("city"),
                "pincode": request.data.get("pincode"),
                "spoken_language": request.data.get("spoken_language"),
            }

            file = request.FILES.get("profile_photo")
            if file:
                temp["profile_photo"] = file.read()             # RAW BYTES
                temp["profile_photo_mimetype"] = file.content_type

            cache.set(personal_key(contact), temp, CACHE_TTL)

            # Hide raw bytes in response
            response_temp = temp.copy()
            if "profile_photo" in response_temp:
                response_temp["profile_photo"] = True
                response_temp["profile_photo_url"] = request.build_absolute_uri(
                    f"/api/trainers/personal/{contact}/view/profile-photo/"
                )

            return api_response(
                True,
                "Step 1 of 4: Personal details saved temporarily.",
                response_temp,
                status_code=200
            )

        # If already exists → normal save
        return super().create(request, *args, **kwargs)

    # ----------------------------------------------------------
    # RETRIEVE (NO FILES IN JSON)
    # ----------------------------------------------------------
    @login_required
    def retrieve(self, request, contact_number=None):
        try:
            trainer = self.get_object()
            data = self.get_serializer(trainer).data

            # Add view + download URLs
            data["profile_photo_url"] = request.build_absolute_uri(
                f"/api/trainers/personal/{contact_number}/view/profile-photo/"
            )
            data["download_profile_photo_url"] = request.build_absolute_uri(
                f"/api/trainers/personal/{contact_number}/download/profile-photo/"
            )

            return api_response(True, "Permanent trainer data", data)
        except:
            pass

        # TEMP fallback
        temp = cache.get(personal_key(contact_number))
        if temp:
            resp = temp.copy()
            if temp.get("profile_photo"):
                resp["profile_photo"] = True
                resp["profile_photo_url"] = request.build_absolute_uri(
                    f"/api/trainers/personal/{contact_number}/view/profile-photo/"
                )
            return api_response(True, "Temporary trainer data", resp)

        return api_response(False, "Trainer not found.", status_code=404)

    # ----------------------------------------------------------
    # VIEW RAW PHOTO (NO BASE64)
    # ----------------------------------------------------------
    @action(detail=True, methods=['get'], url_path="view/profile-photo")
    def view_profile_photo(self, request, contact_number=None):

        # Permanent
        try:
            trainer = self.get_object()
            if trainer.profile_photo:
                return HttpResponse(
                    trainer.profile_photo,
                    content_type=trainer.profile_photo_mimetype or "image/jpeg"
                )
        except:
            pass

        # Temporary
        temp = cache.get(personal_key(contact_number))
        if temp and temp.get("profile_photo"):
            return HttpResponse(
                temp["profile_photo"],
                content_type=temp.get("profile_photo_mimetype") or "image/jpeg"
            )

        return api_response(False, "Profile photo not found.", status_code=404)

    # ----------------------------------------------------------
    # DOWNLOAD RAW PHOTO (NO BASE64)
    # ----------------------------------------------------------
    @login_required
    @action(detail=True, methods=['get'], url_path="download/profile-photo")
    def download_profile_photo(self, request, contact_number=None):

        trainer = self.get_object()

        if trainer.profile_photo:
            resp = HttpResponse(trainer.profile_photo, content_type="application/octet-stream")
            resp["Content-Disposition"] = 'attachment; filename="profile_photo.jpg"'
            return resp

        temp = cache.get(personal_key(contact_number))
        if temp and temp.get("profile_photo"):
            resp = HttpResponse(temp["profile_photo"], content_type="application/octet-stream")
            resp["Content-Disposition"] = 'attachment; filename="profile_photo_temp.jpg"'
            return resp

        return api_response(False, "Profile photo not found.", status_code=404)

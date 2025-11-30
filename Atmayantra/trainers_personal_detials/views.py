from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from datetime import datetime

from .models import TrainerPersonalDetails
from .serializers import TrainerPersonalDetailSerializer

# Authentication imports
from rest_framework_simplejwt.authentication import JWTAuthentication
from authapp.decorators import login_required
from common.permissions import IsAuthenticatedOrPostOnly
from rest_framework.permissions import IsAuthenticated, AllowAny


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

    # CUSTOM PERMISSION LOGIC
    def get_permissions(self):
        """
        POST and view/profile-photo → No Auth
        All other endpoints → Require login
        """
        if self.action in ["create", "view_profile_photo"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    # ----------------------------------------------------------
    # STEP 1: TEMPORARY PERSONAL DETAILS (NO AUTH)
    # ----------------------------------------------------------
    def create(self, request, *args, **kwargs):
        contact = request.data.get("contact_number")
        if not contact:
            return Response({"error": "contact_number is required"}, status=400)

        if not TrainerPersonalDetails.objects.filter(contact_number=contact).exists():

            # Fix the date
            try:
                dob = normalize_date(request.data.get("date_of_birth"))
            except ValueError as e:
                return Response({"error": str(e)}, status=400)

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

            # Photo store
            file = request.FILES.get("profile_photo")
            if file:
                temp["profile_photo"] = file.read()
                temp["profile_photo_mimetype"] = file.content_type

            cache.set(personal_key(contact), temp, CACHE_TTL)

            temp_display = temp.copy()
            if "profile_photo" in temp_display:
                temp_display["profile_photo"] = True

            return Response(
                {
                    "message": "Step 1 of 4: Personal details saved temporarily.",
                    "temporary_data": temp_display
                }, status=200
            )

        return super().create(request, *args, **kwargs)

    # ----------------------------------------------------------
    # RETRIEVE — (AUTH REQUIRED)
    # ----------------------------------------------------------
    @login_required
    def retrieve(self, request, contact_number=None):

        try:
            trainer = self.get_object()
            serializer = self.get_serializer(trainer)
            return Response(serializer.data)
        except:
            pass

        # Temporary fallback
        temp = cache.get(personal_key(contact_number))
        if temp:
            display_temp = temp.copy()
            if temp.get("profile_photo"):
                display_temp["profile_photo"] = True
                display_temp["profile_photo_url"] = request.build_absolute_uri(
                    f"/api/trainers/personal/{contact_number}/view/profile-photo/"
                )
            return Response({"temporary": display_temp})

        return Response({"detail": "Trainer not found."}, status=404)

    # ----------------------------------------------------------
    # VIEW PHOTO → NO LOGIN REQUIRED
    # ----------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='view/profile-photo')
    def view_profile_photo(self, request, contact_number=None):

        try:
            trainer = self.get_object()
            if trainer.profile_photo:
                return HttpResponse(
                    trainer.profile_photo,
                    content_type=trainer.profile_photo_mimetype or "image/jpeg"
                )
        except:
            pass

        temp = cache.get(personal_key(contact_number))
        if temp and temp.get("profile_photo"):
            return HttpResponse(
                temp["profile_photo"],
                content_type=temp.get("profile_photo_mimetype") or "image/jpeg"
            )

        return Response({"detail": "Profile photo not found."}, status=404)

    # ----------------------------------------------------------
    # DOWNLOAD PHOTO — AUTH REQUIRED
    # ----------------------------------------------------------
    @login_required
    @action(detail=True, methods=['get'], url_path='download/profile-photo')
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

        return Response({"detail": "Profile photo not found."}, status=404)

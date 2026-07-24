from django.core.cache import cache
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from authapp.decorators import login_required
from Atmayantra.utils import api_response   # ✅ using api_response now

from .models import TrainerCertification
from .serializers import TrainerCertificationSerializer
from trainers_profile.trainers_personal_detials.models import TrainerPersonalDetails

import uuid
from datetime import datetime

CACHE_TTL = 60 * 60 * 24  # 24 hours

def personal_key(cn): 
    return f"trainer_personal_details_{cn}"

def cert_key(cn): 
    return f"trainer_certification_{cn}"

def to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower().strip() in ("true", "1", "yes")


class TrainerCertificationViewSet(viewsets.ModelViewSet):
    serializer_class = TrainerCertificationSerializer
    queryset = TrainerCertification.objects.all()
    permission_classes = [permissions.AllowAny]
    lookup_field = 'trainer'
    lookup_url_kwarg = 'contact_number'

    # ---------------------------------------------------------
    # STEP 2 OF 4 → CREATE TEMP OR PERMANENT CERTIFICATION
    # ---------------------------------------------------------
    def create(self, request, *args, **kwargs):
        contact = request.data.get("trainer")

        if not contact:
            return api_response(False, "trainer (contact_number) is required", status_code=400)

        trainer_exists = TrainerPersonalDetails.objects.filter(contact_number=contact).exists()
        temp_exists = cache.get(personal_key(contact))

        # -------------------------------------------
        #  TEMPORARY CERTIFICATION SAVE
        # -------------------------------------------
        if not trainer_exists:
            if not temp_exists:
                return api_response(False, "Step 1 must be completed (personal details).", status_code=400)

            cert_list = cache.get(cert_key(contact), [])

            cert_entry = {
                "id": uuid.uuid4().hex,
                "highest_degree": request.data.get("highest_degree"),
                "specialization": request.data.get("specialization"),
                "year_of_graduation": request.data.get("year_of_graduation"),
                "work_experience": request.data.get("work_experience"),
                "yoga_certified": to_bool(request.data.get("yoga_certified")),
                "registration_number": request.data.get("registration_number"),
                "certification_type": request.data.get("certification_type"),
                "issuing_authority": request.data.get("issuing_authority"),
                "created_at": datetime.utcnow().isoformat(),
            }

            cert_list.append(cert_entry)
            cache.set(cert_key(contact), cert_list, CACHE_TTL)

            return api_response(
                True,
                "Step 2 of 4: Certification saved temporarily.",
                {"temporary_item": cert_entry},
                status_code=200
            )

        # -------------------------------------------
        #  PERMANENT SAVE
        # -------------------------------------------
        trainer_obj = TrainerPersonalDetails.objects.get(contact_number=contact)

        data = request.data.copy()
        data["trainer"] = trainer_obj.contact_number
        data["yoga_certified"] = to_bool(request.data.get("yoga_certified"))

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return api_response(False, "Invalid certification data", serializer.errors, status_code=400)

        saved = serializer.save()

        return api_response(
            True,
            "Certification saved successfully.",
            self.get_serializer(saved).data,
            status_code=200  # ❗ You requested 200 OK instead of 201
        )

    # ---------------------------------------------------------
    # LIST ALL CERTIFICATIONS (Login Required)
    # ---------------------------------------------------------
    @login_required
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Certification list retrieved", serializer.data)

    # ---------------------------------------------------------
    # RETRIEVE CERTIFICATION BY ID (Login Required)
    # ---------------------------------------------------------
    @login_required
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Certification retrieved", serializer.data)

    # ---------------------------------------------------------
    # GET ALL CERTIFICATIONS FOR A TRAINER
    # ---------------------------------------------------------
    @login_required
    @action(detail=False, methods=['get'], url_path='list/(?P<contact_number>[^/.]+)')
    def list_certifications(self, request, contact_number=None):

        trainer_exists = TrainerPersonalDetails.objects.filter(contact_number=contact_number).exists()

        if trainer_exists:
            certs = TrainerCertification.objects.filter(trainer_id=contact_number)
            serializer = self.get_serializer(certs, many=True)
            return api_response(True, "Permanent certifications found", serializer.data)

        temp_list = cache.get(cert_key(contact_number))
        if temp_list:
            return api_response(True, "Temporary certifications found", temp_list)

        return api_response(False, "No certifications found.", status_code=404)

    # ---------------------------------------------------------
    # UPDATE (Login Required)
    # ---------------------------------------------------------
    @login_required
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid data", serializer.errors, status_code=400)

        serializer.save()
        return api_response(True, "Certification updated", serializer.data)

    # ---------------------------------------------------------
    # PARTIAL UPDATE (PATCH)
    # ---------------------------------------------------------
    @login_required
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_response(False, "Invalid data", serializer.errors, status_code=400)

        serializer.save()
        return api_response(True, "Certification partially updated", serializer.data)

    # ---------------------------------------------------------
    # DELETE CERTIFICATION
    # ---------------------------------------------------------
    @login_required
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_response(True, "Certification deleted successfully", status_code=200)

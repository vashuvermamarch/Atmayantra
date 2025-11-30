from django.core.cache import cache
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from authapp.decorators import login_required
from .models import TrainerCertification
from .serializers import TrainerCertificationSerializer
from trainers_personal_detials.models import TrainerPersonalDetails
import uuid
from datetime import datetime

CACHE_TTL = 60 * 60 * 24  # 24 hours


def personal_key(cn): return f"trainer_personal_details_{cn}"
def cert_key(cn): return f"trainer_certification_{cn}"


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
    # POST (TEMP + FINAL SAVE) → NO LOGIN REQUIRED
    # ---------------------------------------------------------
    def create(self, request, *args, **kwargs):
        contact = request.data.get("trainer")
        if not contact:
            return Response({"error": "trainer (contact_number) is required"}, status=400)

        trainer_exists = TrainerPersonalDetails.objects.filter(contact_number=contact).exists()
        temp_exists = cache.get(personal_key(contact))

        if not trainer_exists:
            if not temp_exists:
                return Response({"error": "Step 1 must be completed (personal details)."}, status=400)

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

            return Response(
                {"message": "Step 2 of 4: Certification saved temporarily.",
                 "temporary_item": cert_entry},
                status=200
            )

        trainer_obj = TrainerPersonalDetails.objects.get(contact_number=contact)

        data = request.data.copy()
        data["trainer"] = trainer_obj.contact_number
        data["yoga_certified"] = to_bool(request.data.get("yoga_certified"))

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)

    # ---------------------------------------------------------
    # GET LIST (ALL CERTIFICATIONS) → LOGIN REQUIRED
    # ---------------------------------------------------------
    @login_required
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    # ---------------------------------------------------------
    # GET SINGLE CERTIFICATION (retrieve) → LOGIN REQUIRED
    # ---------------------------------------------------------
    @login_required
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    # ---------------------------------------------------------
    # LIST CERTIFICATIONS FOR SPECIFIC TRAINER
    # ---------------------------------------------------------
    @login_required
    @action(detail=False, methods=['get'], url_path='list/(?P<contact_number>[^/.]+)')
    def list_certifications(self, request, contact_number=None):
        trainer_exists = TrainerPersonalDetails.objects.filter(contact_number=contact_number).exists()
        if trainer_exists:
            certs = TrainerCertification.objects.filter(trainer_id=contact_number)
            serializer = self.get_serializer(certs, many=True)
            return Response({"permanent": serializer.data})

        temp_list = cache.get(cert_key(contact_number))
        if temp_list:
            return Response({"temporary": temp_list})

        return Response({"detail": "No certifications found."}, status=404)

    # ---------------------------------------------------------
    # UPDATE / PARTIAL UPDATE → LOGIN REQUIRED
    # ---------------------------------------------------------
    @login_required
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @login_required
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    # ---------------------------------------------------------
    # DELETE → LOGIN REQUIRED
    # ---------------------------------------------------------
    @login_required
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

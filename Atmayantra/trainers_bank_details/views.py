from Atmayantra.utils import api_response
from authapp.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.http import Http404, HttpResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from trainers_certifications.models import TrainerCertification
from trainers_documents.models import TrainerDocument
from trainers_personal_detials.models import TrainerPersonalDetails

from .models import TrainerBankDetails
from .serializers import TrainerBankDetailsSerializer

CACHE_TTL = 60 * 60 * 24


def personal_key(cn): return f"trainer_personal_details_{cn}"
def cert_key(cn): return f"trainer_certification_{cn}"
def docs_key(cn): return f"trainer_documents_{cn}"


class TrainerBankDetailsViewSet(viewsets.ModelViewSet):
    serializer_class = TrainerBankDetailsSerializer
    queryset = TrainerBankDetails.objects.all()
    permission_classes = [permissions.AllowAny]
    lookup_field = "trainer"

    # -------------------------------------------------------------------
    # POST → FINAL SUBMISSION (DO NOT CHANGE RESPONSE)
    # -------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        contact = request.data.get("trainer")

        if not contact:
            return api_response(False, "trainer (contact_number) is required", status_code=400)

        temp_personal = cache.get(personal_key(contact))
        temp_certs = cache.get(cert_key(contact), [])
        temp_docs = cache.get(docs_key(contact), [])

        if not temp_personal:
            return api_response(False, "Step 1 not completed.", status_code=400)

        with transaction.atomic():

            # ----- PERSONAL -----
            trainer = TrainerPersonalDetails.objects.create(
                contact_number=temp_personal["contact_number"],
                full_name=temp_personal["full_name"],
                date_of_birth=temp_personal.get("date_of_birth"),
                gender=temp_personal.get("gender"),
                email=temp_personal.get("email"),
                state=temp_personal.get("state"),
                city=temp_personal.get("city"),
                pincode=temp_personal.get("pincode"),
                spoken_language=temp_personal.get("spoken_language"),
                profile_photo=temp_personal.get("profile_photo"),
                profile_photo_mimetype=temp_personal.get("profile_photo_mimetype"),
            )

            # ----- CERTIFICATIONS -----
            for cert in temp_certs:
                TrainerCertification.objects.create(
                    trainer=trainer,
                    highest_degree=cert.get("highest_degree"),
                    specialization=cert.get("specialization"),
                    year_of_graduation=cert.get("year_of_graduation"),
                    work_experience=cert.get("work_experience"),
                    yoga_certified=cert.get("yoga_certified", False),
                    registration_number=cert.get("registration_number"),
                    certification_type=cert.get("certification_type"),
                    issuing_authority=cert.get("issuing_authority"),
                )

            # ----- DOCUMENTS (BINARY) -----
            for doc in temp_docs:
                TrainerDocument.objects.create(
                    trainer=trainer,
                    document_type=doc.get("document_type"),
                    side=doc.get("side"),
                    document_file=doc.get("document_file"),    # bytes
                    document_mimetype=doc.get("document_mimetype"),
                )

            # ----- BANK DETAILS -----
            data = request.data.copy()
            data["trainer"] = trainer.contact_number

            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                return api_response(False, "Invalid bank details", serializer.errors, status_code=400)

            serializer.save()

        # Clear caches
        cache.delete(personal_key(contact))
        cache.delete(cert_key(contact))
        cache.delete(docs_key(contact))

        # ★★★★★ DO NOT CHANGE THIS MESSAGE ★★★★★
        message = {
            "en": (
                "All steps have been successfully submitted. Your account will be activated once an "
                "administrator reviews and approves your details. You will be notified by our team "
                "when your account is ready. Thank you for completing the registration process."
            ),
            "hi": (
                "सभी चरण सफलतापूर्वक सबमिट हो गए हैं। आपका खाता तब सक्रिय किया जाएगा जब एक "
                "प्रशासक आपकी जानकारी की समीक्षा और स्वीकृति करेगा। आपका खाता तैयार होने पर "
                "हमारी टीम आपको सूचित करेगी। पंजीकरण प्रक्रिया पूरी करने के लिए धन्यवाद।"
            )
        }

        return api_response(True, message, status_code=200)

    # -------------------------------------------------------------------
    # PROTECTED CRUD (no changes)
    # -------------------------------------------------------------------
    @login_required
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return api_response(True, "Bank details list retrieved.", serializer.data)

    @login_required
    def retrieve(self, request, *args, **kwargs):
        bank = self.get_object()
        serializer = self.get_serializer(bank)
        return api_response(True, "Bank details retrieved.", serializer.data)

    @login_required
    def update(self, request, *args, **kwargs):
        bank = self.get_object()
        serializer = self.get_serializer(bank, data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid data", serializer.errors, status_code=400)

        serializer.save()
        return api_response(True, "Bank details updated.", serializer.data)

    @login_required
    def partial_update(self, request, *args, **kwargs):
        bank = self.get_object()
        serializer = self.get_serializer(bank, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_response(False, "Invalid data", serializer.errors, status_code=400)

        serializer.save()
        return api_response(True, "Bank details partially updated.", serializer.data)

    @login_required
    def destroy(self, request, *args, **kwargs):
        bank = self.get_object()
        bank.delete()
        return api_response(True, "Bank details deleted successfully.", status_code=200)

    # -------------------------------------------------------------------
    # QR VIEW → RETURN RAW BYTES (NO BASE64)
    # -------------------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='view-qr')
    def view_qr(self, request, trainer=None):
        bank = self.get_object()

        if not bank.qr_code:
            raise Http404("QR code not found.")

        # Return actual PNG bytes
        return HttpResponse(bank.qr_code, content_type=bank.qr_code_mimetype)

    # -------------------------------------------------------------------
    # QR DOWNLOAD → RETURN FILE (NO BASE64)
    # -------------------------------------------------------------------
    @login_required
    @action(detail=True, methods=['get'], url_path='download-qr')
    def download_qr(self, request, trainer=None):
        bank = self.get_object()

        if not bank.qr_code:
            raise Http404("QR code not found.")

        response = HttpResponse(bank.qr_code, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="qr_code_{trainer}.png"'

        return response

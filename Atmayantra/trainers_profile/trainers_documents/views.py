import uuid
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from authapp.decorators import login_required
# Code add with me
from authapp.authentication import SoftJWTAuthentication
#======================
from Atmayantra.utils import api_response

from trainers_profile.trainers_personal_detials.models import TrainerPersonalDetails
from .models import TrainerDocument
from .serializers import TrainerDocumentSerializer


CACHE_TTL = 60 * 60 * 24  # 24 hours


def personal_key(cn):
    return f"trainer_personal_details_{cn}"


def docs_key(cn):
    return f"trainer_documents_{cn}"


class TrainerDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = TrainerDocumentSerializer
    permission_classes = [permissions.AllowAny]
    # Code add with me
    # SoftJWTAuthentication: inactive user token pe 401 nahi aayega
    authentication_classes = [SoftJWTAuthentication]
    #======================

    # --------------------------------------------------------------------
    # FILTER DOCUMENTS BY trainer CONTACT NUMBER
    # --------------------------------------------------------------------
    def get_queryset(self):
        contact_number = self.kwargs.get("contact_number")
        qs = TrainerDocument.objects.all()

        if contact_number:
            qs = qs.filter(trainer__contact_number=contact_number)

        return qs

    # --------------------------------------------------------------------
    # CREATE → TEMPORARY OR PERMANENT SAVE
    # --------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        trainer_contact = request.data.get("trainer")

        if not trainer_contact:
            return api_response(False, "trainer (contact_number) is required", status_code=400)

        trainer_exists = TrainerPersonalDetails.objects.filter(
            contact_number=trainer_contact
        ).exists()

        # ---------------------- TEMPORARY SAVE --------------------------
        if not trainer_exists:

            if not cache.get(personal_key(trainer_contact)):
                return api_response(False, "Step 1 must be completed first.", status_code=400)

            file = request.FILES.get("document_file")
            if not file:
                return api_response(False, "document_file is required", status_code=400)

            temp_list = cache.get(docs_key(trainer_contact), [])

            temp_doc = {
                "id": uuid.uuid4().hex,
                "document_type": request.data.get("document_type"),
                "side": request.data.get("side"),
                "document_file": file.read(),    # <-- BYTES (Correct)
                "document_mimetype": file.content_type,
            }

            temp_list.append(temp_doc)
            cache.set(docs_key(trainer_contact), temp_list, CACHE_TTL)

            return api_response(
                True,
                "Step 3 of 4: Document saved temporarily.",
                {"temporary_id": temp_doc["id"]},
                status_code=200
            )

        # ---------------------- PERMANENT SAVE --------------------------
        trainer_obj = TrainerPersonalDetails.objects.get(contact_number=trainer_contact)

        data = request.data.copy()
        data["trainer"] = trainer_obj.contact_number

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        saved = serializer.save()

        return api_response(True, "Document saved successfully.", self.get_serializer(saved).data)

    # --------------------------------------------------------------------
    # LIST DOCUMENTS
    # --------------------------------------------------------------------
    @login_required
    def list(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")

        if not contact_number:
            qs = TrainerDocument.objects.all()
            serializer = self.get_serializer(qs, many=True)
            return api_response(True, "All documents retrieved", serializer.data)

        # Check if trainer exists → load permanent
        if TrainerPersonalDetails.objects.filter(contact_number=contact_number).exists():
            qs = TrainerDocument.objects.filter(trainer__contact_number=contact_number)
            serializer = self.get_serializer(qs, many=True)
            return api_response(True, "Permanent documents found", serializer.data)

        # Otherwise → Temporary
        temp_docs = cache.get(docs_key(contact_number))
        if temp_docs:
            return api_response(True, "Temporary documents found", temp_docs)

        return api_response(False, "No documents found.", status_code=404)

    # --------------------------------------------------------------------
    # VIEW DOCUMENT AS RAW FILE
    # --------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="view")
    def view(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")
        pk = self.kwargs.get("pk")

        # Permanent
        try:
            doc = self.get_object()
            return HttpResponse(doc.document_file, content_type=doc.document_mimetype)
        except:
            pass

        # Temporary
        temp_docs = cache.get(docs_key(contact_number), [])
        for doc in temp_docs:
            if doc["id"] == pk:
                return HttpResponse(doc["document_file"], content_type=doc["document_mimetype"])

        return api_response(False, "Document not found.", status_code=404)

    # --------------------------------------------------------------------
    # DOWNLOAD DOCUMENT AS ATTACHMENT
    # --------------------------------------------------------------------
    @login_required
    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")
        pk = self.kwargs.get("pk")

        # Permanent
        try:
            doc = self.get_object()
            response = HttpResponse(doc.document_file, content_type="application/octet-stream")
            response["Content-Disposition"] = f'attachment; filename="{doc.document_type}_{doc.id}.pdf"'
            return response
        except:
            pass

        # Temporary
        temp_docs = cache.get(docs_key(contact_number), [])
        for doc in temp_docs:
            if doc["id"] == pk:
                response = HttpResponse(doc["document_file"], content_type="application/octet-stream")
                response["Content-Disposition"] = f'attachment; filename="{doc["document_type"]}_{doc["id"]}.pdf"'
                return response

        return api_response(False, "Document not found.", status_code=404)

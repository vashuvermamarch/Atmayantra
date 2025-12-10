import base64
import uuid
from django.core.cache import cache
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from authapp.decorators import login_required
from Atmayantra.utils import api_response

from trainers_personal_detials.models import TrainerPersonalDetails
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

    # --------------------------------------------------------
    # FILTER DOCUMENTS BASED ON trainer CONTACT NUMBER
    # --------------------------------------------------------
    def get_queryset(self):
        contact_number = self.kwargs.get("contact_number")
        qs = TrainerDocument.objects.all()

        if contact_number:
            qs = qs.filter(trainer__contact_number=contact_number)

        return qs

    # --------------------------------------------------------
    # CREATE → TEMP OR PERMANENT SAVE
    # --------------------------------------------------------
    def create(self, request, *args, **kwargs):
        trainer_contact = request.data.get("trainer")

        if not trainer_contact:
            return api_response(False, "trainer (contact_number) is required", status_code=400)

        trainer_exists = TrainerPersonalDetails.objects.filter(
            contact_number=trainer_contact
        ).exists()

        # -----------------------------------------
        # TEMPORARY SAVE (Step 3 of 4)
        # -----------------------------------------
        if not trainer_exists:

            if not cache.get(personal_key(trainer_contact)):
                return api_response(False, "Step 1 must be completed (personal details).", status_code=400)

            file = request.FILES.get("document_file")
            if not file:
                return api_response(False, "document_file is required", status_code=400)

            temp_list = cache.get(docs_key(trainer_contact), [])

            temp_doc = {
                "id": uuid.uuid4().hex,
                "document_type": request.data.get("document_type"),
                "side": request.data.get("side"),
                "document_file": base64.b64encode(file.read()).decode(),
                "document_mimetype": file.content_type,
            }

            temp_list.append(temp_doc)
            cache.set(docs_key(trainer_contact), temp_list, CACHE_TTL)

            return api_response(
                True,
                "Step 3 of 4: Document saved temporarily.",
                {"temporary_item": temp_doc},
                status_code=200
            )

        # -----------------------------------------
        # PERMANENT SAVE
        # -----------------------------------------
        trainer_obj = TrainerPersonalDetails.objects.get(contact_number=trainer_contact)

        data = request.data.copy()
        data["trainer"] = trainer_obj.contact_number

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return api_response(False, "Invalid document data", serializer.errors, status_code=400)

        saved = serializer.save()

        return api_response(
            True,
            "Document saved successfully.",
            self.get_serializer(saved).data,
            status_code=200  # You requested 200 OK for success
        )

    # --------------------------------------------------------
    # LIST → LOGIN REQUIRED
    # --------------------------------------------------------
    @login_required
    def list(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")

        # NO contact_number → return all permanent docs
        if not contact_number:
            qs = TrainerDocument.objects.all()
            serializer = self.get_serializer(qs, many=True)
            return api_response(True, "All documents retrieved", serializer.data)

        trainer_exists = TrainerPersonalDetails.objects.filter(
            contact_number=contact_number
        ).exists()

        # PERMANENT DOCUMENTS
        if trainer_exists:
            qs = TrainerDocument.objects.filter(trainer__contact_number=contact_number)
            serializer = self.get_serializer(qs, many=True)
            return api_response(True, "Permanent documents found", serializer.data)

        # TEMPORARY DOCUMENTS
        temp_docs = cache.get(docs_key(contact_number))
        if temp_docs:
            return api_response(True, "Temporary documents found", temp_docs)

        return api_response(False, "No documents found.", status_code=404)

    # --------------------------------------------------------
    # VIEW DOCUMENT → RETURN BASE64 JSON (NOT BINARY)
    # --------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="view")
    def view(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")
        pk = self.kwargs.get("pk")

        # PERMANENT DOCUMENT
        try:
            doc = self.get_object()
            return api_response(
                True,
                "Document retrieved",
                {
                    "document_type": doc.document_type,
                    "file": base64.b64encode(doc.document_file).decode(),
                    "mimetype": doc.document_mimetype,
                }
            )
        except:
            pass

        # TEMPORARY DOCUMENT
        temp_docs = cache.get(docs_key(contact_number), [])
        for doc in temp_docs:
            if doc["id"] == pk:
                return api_response(
                    True,
                    "Temporary document retrieved",
                    {
                        "document_type": doc["document_type"],
                        "file": doc["document_file"],
                        "mimetype": doc["document_mimetype"],
                    }
                )

        return api_response(False, "Document not found.", status_code=404)

    # --------------------------------------------------------
    # DOWNLOAD DOCUMENT → RETURN BASE64 JSON (NOT FILE STREAM)
    # --------------------------------------------------------
    @login_required
    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")
        pk = self.kwargs.get("pk")

        # PERMANENT
        try:
            doc = self.get_object()
            return api_response(
                True,
                "Document ready for download",
                {
                    "filename": f"{doc.document_type}_{doc.id}.pdf",
                    "file": base64.b64encode(doc.document_file).decode()
                }
            )
        except:
            pass

        # TEMPORARY
        temp_docs = cache.get(docs_key(contact_number), [])
        for doc in temp_docs:
            if doc["id"] == pk:
                return api_response(
                    True,
                    "Temporary document ready for download",
                    {
                        "filename": f"{doc['document_type']}_{doc['id']}.pdf",
                        "file": doc["document_file"]
                    }
                )

        return api_response(False, "Document not found.", status_code=404)

from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from authapp.decorators import login_required
from trainers_personal_detials.models import TrainerPersonalDetails
from .models import TrainerDocument
from .serializers import TrainerDocumentSerializer
import uuid

CACHE_TTL = 60 * 60 * 24  # 24 hours


def personal_key(cn):
    return f"trainer_personal_details_{cn}"


def docs_key(cn):
    return f"trainer_documents_{cn}"


class TrainerDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = TrainerDocumentSerializer
    permission_classes = [permissions.AllowAny]

    # --------------------------------------------------------------------
    # CORRECT get_queryset → ensures filtering by URL trainer parameter
    # --------------------------------------------------------------------
    def get_queryset(self):
        contact_number = self.kwargs.get("contact_number")
        qs = TrainerDocument.objects.all()

        if contact_number:
            qs = qs.filter(trainer__contact_number=contact_number)

        return qs

    # --------------------------------------------------------------------
    # CREATE → TEMP OR PERMANENT
    # --------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        trainer_contact = request.data.get("trainer")
        if not trainer_contact:
            return Response({"error": "trainer (contact_number) is required"}, status=400)

        trainer_exists = TrainerPersonalDetails.objects.filter(
            contact_number=trainer_contact
        ).exists()

        # ---------------------- TEMPORARY SAVE ----------------------
        if not trainer_exists:

            if not cache.get(personal_key(trainer_contact)):
                return Response(
                    {"error": "Step 1 must be completed (personal details)."},
                    status=400,
                )

            file = request.FILES.get("document_file")
            if not file:
                return Response({"error": "document_file is required"}, status=400)

            temp_list = cache.get(docs_key(trainer_contact), [])

            temp_doc = {
                "id": uuid.uuid4().hex,
                "document_type": request.data.get("document_type"),
                "side": request.data.get("side"),
                "document_file": file.read(),
                "document_mimetype": file.content_type,
            }

            temp_list.append(temp_doc)
            cache.set(docs_key(trainer_contact), temp_list, CACHE_TTL)

            return Response(
                {"message": "Step 3 of 4: Document saved temporarily.",
                 "temporary_id": temp_doc["id"]},
                status=200,
            )

        # ---------------------- PERMANENT SAVE ----------------------
        trainer_obj = TrainerPersonalDetails.objects.get(contact_number=trainer_contact)

        data = request.data.copy()
        data["trainer"] = trainer_obj.contact_number

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)

    # --------------------------------------------------------------------
    # LIST DOCUMENTS → LOGIN REQUIRED
    # --------------------------------------------------------------------
    @login_required
    def list(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")

        # -------------------- CASE 1: /documents/ (all docs) --------------------
        if not contact_number:
            qs = TrainerDocument.objects.all()
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)

        # -------------------- CASE 2: /documents/<contact>/ --------------------
        trainer_exists = TrainerPersonalDetails.objects.filter(
            contact_number=contact_number
        ).exists()

        # Permanent documents
        if trainer_exists:
            qs = TrainerDocument.objects.filter(trainer__contact_number=contact_number)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)

        # Temporary docs
        temp_docs = cache.get(docs_key(contact_number))
        if temp_docs:
            for doc in temp_docs:
                doc["view_url"] = request.build_absolute_uri(
                    f"/api/trainers/documents/{contact_number}/{doc['id']}/view/"
                )
            return Response(temp_docs)

        return Response({"detail": "No documents found."}, status=404)

    # --------------------------------------------------------------------
    # VIEW DOCUMENT → PUBLIC (NO LOGIN REQUIRED)
    # --------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="view")
    def view(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")
        pk = self.kwargs.get("pk")

        # Permanent first
        try:
            doc = self.get_object()
            return HttpResponse(doc.document_file, content_type=doc.document_mimetype)
        except:
            pass

        # Temporary
        temp_docs = cache.get(docs_key(contact_number), [])
        for doc in temp_docs:
            if doc["id"] == pk:
                return HttpResponse(
                    doc["document_file"], content_type=doc["document_mimetype"]
                )

        return Response({"detail": "Document not found."}, status=404)

    # --------------------------------------------------------------------
    # DOWNLOAD → LOGIN REQUIRED
    # --------------------------------------------------------------------
    @login_required
    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, *args, **kwargs):
        contact_number = self.kwargs.get("contact_number")
        pk = self.kwargs.get("pk")

        # Permanent
        try:
            doc = self.get_object()
            response = HttpResponse(
                doc.document_file, content_type="application/octet-stream"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{doc.document_type}_{doc.id}.pdf"'
            )
            return response
        except:
            pass

        # Temporary
        temp_docs = cache.get(docs_key(contact_number), [])
        for doc in temp_docs:
            if doc["id"] == pk:
                response = HttpResponse(
                    doc["document_file"], content_type="application/octet-stream"
                )
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="{doc["document_type"]}_{doc["id"]}.pdf"'
                return response

        return Response({"detail": "Document not found."}, status=404)

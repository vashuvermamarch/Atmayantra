from authapp.decorators import login_required
from django.http import HttpResponse
from managers_profile.manager_personal_details.models import ManagerPersonalDetails
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ManagerDocument


# =========================================================
# HELPER → PER MANAGER DOCUMENT ID
# =========================================================
def get_next_manager_doc_id(personal):

    last_doc = ManagerDocument.objects.filter(
        manager=personal
    ).order_by("-manager_doc_id").first()

    if not last_doc:
        return 1

    return last_doc.manager_doc_id + 1


# =========================================================
# LIST + CREATE DOCUMENTS
# =========================================================
class ManagerDocsView(APIView):

    # ---------------- GET ----------------
    @login_required
    def get(self, request, contact_number=None):

        if contact_number:

            personal = ManagerPersonalDetails.objects.filter(
                contact_number=contact_number
            ).first()

            if not personal:
                return Response({"error": "Manager not found"}, status=404)

            docs = ManagerDocument.objects.filter(manager=personal)

            return Response([
                {
                    "id": d.manager_doc_id,
                    "doc_type": d.doc_type
                }
                for d in docs
            ])

        docs = ManagerDocument.objects.all()

        return Response([
            {
                "id": d.manager_doc_id,
                "doc_type": d.doc_type,
                "manager_contact": d.manager.contact_number
            }
            for d in docs
        ])

    # ---------------- CREATE ----------------
    @login_required
    def post(self, request, contact_number):

        personal = ManagerPersonalDetails.objects.filter(
            contact_number=contact_number
        ).first()

        if not personal:
            return Response({"error": "Manager not found"}, status=404)

        file = request.FILES.get("file")

        if not file:
            return Response({"error": "File required"}, status=400)

        new_doc_id = get_next_manager_doc_id(personal)

        ManagerDocument.objects.create(
            manager=personal,
            manager_doc_id=new_doc_id,
            doc_type=request.data.get("doc_type"),
            file=file.read(),
            file_mimetype=file.content_type
        )

        return Response({
            "message": "Document Uploaded",
            "manager_doc_id": new_doc_id
        })


# =========================================================
# CONTROL DOCUMENT
# =========================================================
class ManagerDocControlView(APIView):

    @login_required
    def get(self, request, contact_number, doc_id):

        personal = ManagerPersonalDetails.objects.filter(
            contact_number=contact_number
        ).first()

        if not personal:
            return Response({"error": "Manager not found"}, status=404)

        doc = ManagerDocument.objects.filter(
            manager=personal,
            manager_doc_id=doc_id
        ).first()

        if not doc:
            return Response({"error": "Document not found"}, status=404)

        response = HttpResponse(
            doc.file,
            content_type=doc.file_mimetype or "application/octet-stream"
        )

        if request.GET.get("download") == "true":
            response['Content-Disposition'] = f'attachment; filename="document_{doc_id}"'

        return response


    @login_required
    def delete(self, request, contact_number, doc_id):

        try:
            personal = ManagerPersonalDetails.objects.filter(
                contact_number=contact_number
            ).first()

            if not personal:
                return Response({
                    "error": "Manager not found"
                }, status=404)

            doc = ManagerDocument.objects.filter(
                manager=personal,
                manager_doc_id=doc_id
            ).first()

            if not doc:
                return Response({
                    "error": "Document not found"
                }, status=404)

            doc.delete()

            return Response({
                "message": "Document deleted successfully"
            })

        except Exception as e:
            return Response({
                "error": str(e)
            }, status=500)


    @login_required
    def put(self, request, contact_number, doc_id):
        return self.update_doc(request, contact_number, doc_id)

    @login_required
    def patch(self, request, contact_number, doc_id):
        return self.update_doc(request, contact_number, doc_id)


    def update_doc(self, request, contact_number, doc_id):

        personal = ManagerPersonalDetails.objects.filter(
            contact_number=contact_number
        ).first()

        if not personal:
            return Response({"error": "Manager not found"}, status=404)

        doc = ManagerDocument.objects.filter(
            manager=personal,
            manager_doc_id=doc_id
        ).first()

        if not doc:
            return Response({"error": "Document not found"}, status=404)

        doc.doc_type = request.data.get("doc_type", doc.doc_type)

        if request.FILES.get("file"):
            f = request.FILES.get("file")
            doc.file = f.read()
            doc.file_mimetype = f.content_type

        doc.save()

        return Response({"message": "Updated"})

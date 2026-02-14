from rest_framework.views import APIView
from authapp.decorators import login_required
from rest_framework.response import Response
from django.http import HttpResponse
from .models import ManagerPersonalDetails


# -------------------------------------------------
# PERSONAL DETAILS (NO BINARY DATA HERE)
# -------------------------------------------------
class ManagerPersonalView(APIView):

    @login_required
    def get(self, request, contact_number=None):

        # -------- SINGLE MANAGER ----------
        if contact_number:
            try:
                obj = ManagerPersonalDetails.objects.get(contact_number=contact_number)

                return Response({
                    "employee_name": obj.employee_name,
                    "contact_number": obj.contact_number,
                    "designation": obj.designation,
                    "email": obj.email,
                    "employee_id": obj.employee_id,
                    "salary": obj.salary,
                    "address": obj.address,
                    "date_of_joining": obj.date_of_joining,
                    "location": obj.location
                })

            except ManagerPersonalDetails.DoesNotExist:
                return Response({"error": "Not Found"}, status=404)

        # -------- ALL MANAGERS ----------
        data = ManagerPersonalDetails.objects.all().values(
            "id",
            "employee_name",
            "employee_id",
            "contact_number",
            "designation",
            "email",
            "salary",
            "address",
            "date_of_joining",
            "location"
        )

        return Response(list(data))


# -------------------------------------------------
# PHOTO VIEW (BINARY STREAM)
# -------------------------------------------------
class ManagerPhotoView(APIView):

    @login_required
    def get(self, request, contact_number):

        try:
            obj = ManagerPersonalDetails.objects.get(contact_number=contact_number)

            return HttpResponse(
                obj.profile_photo,
                content_type=obj.profile_photo_mimetype or "image/jpeg"
            )

        except ManagerPersonalDetails.DoesNotExist:
            return Response({"error": "Not Found"}, status=404)


# -------------------------------------------------
# PHOTO DOWNLOAD
# -------------------------------------------------
class ManagerPhotoDownloadView(APIView):

    @login_required
    def get(self, request, contact_number):

        try:
            obj = ManagerPersonalDetails.objects.get(contact_number=contact_number)

            response = HttpResponse(
                obj.profile_photo,
                content_type=obj.profile_photo_mimetype or "application/octet-stream"
            )

            filename = f"{obj.contact_number}_profile_photo"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            return response

        except ManagerPersonalDetails.DoesNotExist:
            return Response({"error": "Not Found"}, status=404)


# -------------------------------------------------
# UPDATE / DELETE
# -------------------------------------------------
class ManagerUpdateDeleteView(APIView):

    @login_required
    def put(self, request, contact_number):
        return self.update_manager(request, contact_number)

    @login_required
    def patch(self, request, contact_number):
        return self.update_manager(request, contact_number)

    @login_required
    def delete(self, request, contact_number):

        try:
            obj = ManagerPersonalDetails.objects.get(contact_number=contact_number)
            obj.delete()
            return Response({"message": "Deleted"})

        except ManagerPersonalDetails.DoesNotExist:
            return Response({"error": "Not Found"}, status=404)


    def update_manager(self, request, contact_number):

        try:
            obj = ManagerPersonalDetails.objects.get(contact_number=contact_number)

            data = request.data

            obj.employee_name = data.get("employee_name", obj.employee_name)
            obj.designation = data.get("designation", obj.designation)
            obj.email = data.get("email", obj.email)

            # FILE UPDATE
            if request.FILES.get("profile_photo"):
                file = request.FILES.get("profile_photo")
                obj.profile_photo = file.read()
                obj.profile_photo_mimetype = file.content_type

            obj.save()

            return Response({"message": "Updated"})

        except ManagerPersonalDetails.DoesNotExist:
            return Response({"error": "Not Found"}, status=404)

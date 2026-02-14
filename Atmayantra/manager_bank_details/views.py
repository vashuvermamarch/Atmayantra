from rest_framework.views import APIView
from authapp.decorators import login_required
from rest_framework.response import Response
from .models import ManagerBankDetails
from manager_personal_details.models import ManagerPersonalDetails


class ManagerBankView(APIView):

    @login_required
    def get(self, request, contact_number=None):

        if contact_number:
            personal = ManagerPersonalDetails.objects.get(contact_number=contact_number)
            bank = ManagerBankDetails.objects.get(manager=personal)

            return Response({
                "account_holder_name": bank.account_holder_name,
                "bank_name": bank.bank_name,
                "branch_name": bank.branch_name,
                "account_number": bank.account_number,
                "account_type": bank.account_type,
                "upi_id": bank.upi_id,
                "ifsc_code": bank.ifsc_code
            })


        return Response(ManagerBankDetails.objects.all().values())


class ManagerBankUpdateDeleteView(APIView):

    @login_required
    def put(self, request, contact_number):
        return self.update_bank(request, contact_number)

    @login_required
    def patch(self, request, contact_number):
        return self.update_bank(request, contact_number)

    @login_required
    def delete(self, request, contact_number):

        personal = ManagerPersonalDetails.objects.get(contact_number=contact_number)
        bank = ManagerBankDetails.objects.get(manager=personal)

        bank.delete()
        return Response({"message": "Deleted"})


    def update_bank(self, request, contact_number):

        try:
            # -------------------------------------------------
            # GET MANAGER PERSONAL
            # -------------------------------------------------
            personal = ManagerPersonalDetails.objects.get(
                contact_number=contact_number
            )

            # -------------------------------------------------
            # GET BANK RECORD
            # -------------------------------------------------
            bank = ManagerBankDetails.objects.get(
                manager=personal
            )

            # -------------------------------------------------
            # ALL UPDATABLE FIELDS
            # -------------------------------------------------
            fields = [
                "account_holder_name",
                "bank_name",
                "branch_name",
                "account_number",
                "account_type",
                "upi_id",
                "ifsc_code",
            ]

            # -------------------------------------------------
            # UPDATE LOOP (WORKS FOR QueryDict + JSON)
            # -------------------------------------------------
            for field in fields:

                value = request.data.get(field)

                # Fix QueryDict list values
                if isinstance(value, list):
                    value = value[0]

                if value is not None:
                    setattr(bank, field, value)

            # -------------------------------------------------
            # SAVE
            # -------------------------------------------------
            bank.save()

            return Response({
                "message": "Bank details updated successfully"
            })

        except ManagerPersonalDetails.DoesNotExist:
            return Response({
                "error": "Manager not found"
            }, status=404)

        except ManagerBankDetails.DoesNotExist:
            return Response({
                "error": "Bank details not found"
            }, status=404)

        except Exception as e:
            return Response({
                "error": str(e)
            }, status=500)

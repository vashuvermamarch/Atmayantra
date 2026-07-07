from authapp.decorators import login_required
from managers_profile.manager_personal_details.models import ManagerPersonalDetails
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ManagerBankDetails


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

        try:
            personal = ManagerPersonalDetails.objects.filter(
                contact_number=contact_number
            ).first()

            if not personal:
                return Response({
                    "error": "Manager not found"
                }, status=404)

            bank = ManagerBankDetails.objects.filter(
                manager=personal
            ).first()

            if not bank:
                return Response({
                    "error": "Bank details not found"
                }, status=404)

            bank.delete()

            return Response({
                "message": "Bank details deleted successfully"
            })

        except Exception as e:
            return Response({
                "error": str(e)
            }, status=500)



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

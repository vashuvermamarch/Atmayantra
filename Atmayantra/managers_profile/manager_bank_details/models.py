from django.db import models
from managers_profile.manager_personal_details.models import ManagerPersonalDetails


class ManagerBankDetails(models.Model):

    manager = models.OneToOneField(
        ManagerPersonalDetails,
        on_delete=models.CASCADE,
        related_name="bank_details"
    )

    account_holder_name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=20)
    upi_id = models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20)

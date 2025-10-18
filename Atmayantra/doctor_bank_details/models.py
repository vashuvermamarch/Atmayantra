from django.db import models
from doctor_personal_details.models import DoctorPersonalDetails

class DoctorBankDetails(models.Model):
    doctor = models.OneToOneField(
        DoctorPersonalDetails,
        to_field='contact_number',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='bank_details'
    )
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=255)
    upi_id = models.CharField(max_length=255, null=True, blank=True)
    account_type = models.CharField(max_length=50)
    bank_qr_code = models.TextField(null=True, blank=True)  # To store base64 encoded image

    class Meta:
        db_table = 'doctor_bank_details'

    def __str__(self):
        return f"Bank details for {self.doctor.full_name}"
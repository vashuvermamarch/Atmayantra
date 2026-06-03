from django.db import models
from django.conf import settings

class PhysioBankDetails(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='physio_bank_details')
    upload_bank_qr_code = models.ImageField(upload_to='physio_bank_details/qr/', null=True, blank=True)
    account_holder_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    confirm_account_number = models.CharField(max_length=50, null=True, blank=True)
    ifsc_code = models.CharField(max_length=50, null=True, blank=True)
    upi_id = models.CharField(max_length=100, null=True, blank=True)
    account_type = models.CharField(max_length=50, null=True, blank=True)
    net_banking = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Bank Details (Physio)"

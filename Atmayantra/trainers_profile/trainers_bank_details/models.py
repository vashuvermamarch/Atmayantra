from django.db import models

from trainers_profile.trainers_personal_detials.models import TrainerPersonalDetails


class TrainerBankDetails(models.Model):
    """
    Stores bank account details for a trainer.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('SAVING', 'Saving Account'),
        ('CURRENT', 'Current Account'),
    ]

    trainer = models.OneToOneField(
        TrainerPersonalDetails,
        on_delete=models.CASCADE,
        related_name='bank_details'
        # The primary_key=True has been removed. Django will add an 'id' field automatically.
    )
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    upi_id = models.CharField(max_length=100, null=True, blank=True, help_text="Optional UPI ID.")
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES)
    qr_code = models.BinaryField(null=True, blank=True, help_text="QR code image stored as binary data.")
    qr_code_mimetype = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'trainers_bank_details'
        verbose_name = "Trainer Bank Detail"

    def __str__(self):
        return f"Bank Details for {self.trainer.full_name}"

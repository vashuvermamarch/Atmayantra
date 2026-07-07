from django.db import models

from trainers_profile.trainers_personal_detials.models import TrainerPersonalDetails


class TrainerDocument(models.Model):
    """
    Stores documents for a trainer, like Aadhar, PAN card, etc.
    """
    DOCUMENT_TYPES = [
        ('AADHAR', 'Aadhar Card'),
        ('PAN', 'PAN Card'),
        ('RESUME_CV', 'Resume/CV'),
        ('CERTIFICATION', 'Certification'),
        ('OTHER', 'Other'),
    ]

    SIDE_CHOICES = [
        ('FRONT', 'Front'),
        ('BACK', 'Back'),
    ]

    trainer = models.ForeignKey(
        TrainerPersonalDetails,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES, null=True, blank=True, help_text="Only for documents like Aadhar/PAN card")
    document_file = models.BinaryField()
    document_mimetype = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trainers_documents'
        ordering = ['trainer', 'uploaded_at']
        verbose_name = "Trainer Document"

    def __str__(self):
        return f"{self.get_document_type_display()} for {self.trainer.full_name}"

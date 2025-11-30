from django.db import models
from trainers_personal_detials.models import TrainerPersonalDetails

class TrainerCertification(models.Model):
    trainer = models.ForeignKey(
        TrainerPersonalDetails,
        on_delete=models.CASCADE,
        related_name='certifications'
    )
    highest_degree = models.CharField(max_length=255, blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    year_of_graduation = models.PositiveIntegerField(null=True, blank=True)
    work_experience = models.PositiveIntegerField(null=True, blank=True)
    yoga_certified = models.BooleanField(default=False)
    registration_number = models.CharField(max_length=100, blank=True)
    certification_type = models.CharField(max_length=255, blank=True)
    issuing_authority = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'trainers_certifications'
        verbose_name = "Trainer Certification"

    def __str__(self):
        return f"Certification for {self.trainer.full_name}"

from django.db import models
from django.conf import settings

class PhysioCertification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='physio_certification')
    highest_degree = models.CharField(max_length=255, null=True, blank=True)
    specializations = models.CharField(max_length=255, null=True, blank=True)
    year_of_graduation = models.CharField(max_length=10, null=True, blank=True)
    work_experience = models.CharField(max_length=255, null=True, blank=True)
    is_certified_licensed = models.CharField(max_length=50, null=True, blank=True)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    certification_type = models.CharField(max_length=100, null=True, blank=True)
    issuing_authority = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Certification (Physio)"

from django.conf import settings
from django.db import models


class PhysioDocumentation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='physio_documentation')
    aadhar_card_front = models.BinaryField(null=True, blank=True)
    aadhar_card_front_mimetype = models.CharField(max_length=100, null=True, blank=True)
    aadhar_card_back = models.BinaryField(null=True, blank=True)
    aadhar_card_back_mimetype = models.CharField(max_length=100, null=True, blank=True)
    pancard = models.BinaryField(null=True, blank=True)
    pancard_mimetype = models.CharField(max_length=100, null=True, blank=True)
    resume_cv = models.BinaryField(null=True, blank=True)
    resume_cv_mimetype = models.CharField(max_length=100, null=True, blank=True)
    certificate = models.BinaryField(null=True, blank=True)
    certificate_mimetype = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Documentation (Physio)"

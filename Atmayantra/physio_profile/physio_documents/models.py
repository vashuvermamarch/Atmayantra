from django.db import models
from django.conf import settings

class PhysioDocumentation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='physio_documentation')
    aadhar_card_front = models.ImageField(upload_to='physio_documentation/aadhar/', null=True, blank=True)
    aadhar_card_back = models.ImageField(upload_to='physio_documentation/aadhar/', null=True, blank=True)
    pancard = models.ImageField(upload_to='physio_documentation/pancard/', null=True, blank=True)
    resume_cv = models.FileField(upload_to='physio_documentation/resume/', null=True, blank=True)
    certificate = models.FileField(upload_to='physio_documentation/certificate/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Documentation (Physio)"

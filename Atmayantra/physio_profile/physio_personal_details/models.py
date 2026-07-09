from django.conf import settings
from django.db import models


class PhysioPersonalDetails(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='physio_personal_details')
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    contact_number = models.CharField(max_length=20)
    email_address = models.EmailField()
    state = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    language = models.CharField(max_length=100, null=True, blank=True)
    profile_photo = models.BinaryField(null=True, blank=True)
    profile_photo_mimetype = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}'s Personal Details (Physio)"

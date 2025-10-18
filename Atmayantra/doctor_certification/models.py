from django.db import models
from doctor_personal_details.models import DoctorPersonalDetails

class DoctorCertification(models.Model):
    doctor = models.OneToOneField(DoctorPersonalDetails, on_delete=models.CASCADE, primary_key=True, related_name='certification')

    highest_degree = models.CharField(max_length=255)
    year_of_graduation = models.CharField(max_length=4)
    year_of_experience = models.CharField(max_length=2)
    yoga_certified = models.CharField(max_length=3)
    certification_type = models.CharField(max_length=255)
    issuing_authority = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255)
    license_number = models.CharField(max_length=255)

    graduation_certificate = models.TextField(null=True, blank=True)
    graduation_certificate_filename = models.CharField(max_length=255, null=True, blank=True)
    experience_letter = models.TextField(null=True, blank=True)
    experience_letter_filename = models.CharField(max_length=255, null=True, blank=True)
    resume_cv = models.TextField(null=True, blank=True)
    resume_cv_filename = models.CharField(max_length=255, null=True, blank=True)
    license = models.TextField(null=True, blank=True)
    license_filename = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Certification for {self.doctor.full_name}"
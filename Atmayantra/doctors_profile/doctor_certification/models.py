from django.db import models
from doctors_profile.doctor_personal_details.models import DoctorPersonalDetails

class DoctorCertification(models.Model):
    doctor = models.OneToOneField(DoctorPersonalDetails, on_delete=models.CASCADE, primary_key=True, related_name='certification')
    highest_degree = models.CharField(max_length=100)
    specializations = models.CharField(max_length=255, null=True, blank=True)
    year_of_graduation = models.PositiveIntegerField()
    license_registration_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    year_of_experience = models.PositiveIntegerField()
    yoga_certified = models.BooleanField(default=False)
    certification_type = models.CharField(max_length=100)
    issuing_authority = models.CharField(max_length=255)
    # issue_date = models.DateField(null=True, blank=True)
    # expiration_date = models.DateField(null=True, blank=True)
    graduation_certificate = models.TextField(null=True, blank=True)  # Base64 encoded PDF
    experience_letter = models.TextField(null=True, blank=True)  # Base64 encoded PDF
    resume_cv = models.TextField(null=True, blank=True)  # Base64 encoded PDF
    license_pdf = models.TextField(null=True, blank=True)  # Base64 encoded PDF

    class Meta:
        db_table = 'doctor_certifications'
        verbose_name = "Doctor Certification"
        verbose_name_plural = "Doctor Certifications"

    def __str__(self):
        return f"Certification for {self.doctor.name}"

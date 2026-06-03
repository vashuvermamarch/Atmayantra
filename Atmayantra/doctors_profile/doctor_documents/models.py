from django.db import models
from doctors_profile.doctor_personal_details.models import DoctorPersonalDetails

class DoctorDocument(models.Model):
    doctor = models.ForeignKey(DoctorPersonalDetails, to_field='contact_number', on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=255)
    side = models.CharField(max_length=255, null=True, blank=True)
    filename = models.CharField(max_length=255, null=True, blank=True)
    content_type = models.CharField(max_length=255, null=True, blank=True)
    file_data = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Document {self.filename} for {self.doctor.full_name}"

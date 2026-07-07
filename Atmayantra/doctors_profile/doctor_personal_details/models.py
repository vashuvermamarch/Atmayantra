from django.db import models


class DoctorPersonalDetails(models.Model):
    contact_number = models.CharField(max_length=15, primary_key=True)
    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    # This is the corrected version
    spoken_language = models.CharField(max_length=100, default='', blank=True)


    class Meta:
        db_table = 'doctors_personal_details'
        verbose_name = "Doctor Personal Detail"
        verbose_name_plural = "Doctor Personal Details"

    def __str__(self):
        return f"{self.full_name} ({self.contact_number})"

class DoctorProfilePhoto(models.Model):
    doctor = models.OneToOneField(
        DoctorPersonalDetails,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile_photo_data'
    )
    photo_data = models.TextField()

    def __str__(self):
        return f"Profile photo for {self.doctor.full_name}"

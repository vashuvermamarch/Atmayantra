from django.db import models

class DoctorPersonalDetails(models.Model):
    contact_number = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255)
    experience = models.IntegerField()
    hospital = models.CharField(max_length=255)
    gender = models.CharField(max_length=10)
    email = models.EmailField(unique=True)
    address = models.TextField()
    profile_photo = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'doctors - personal_details'

    def __str__(self):
        return self.full_name
from django.db import models


class TrainerPersonalDetails(models.Model):
    """
    Stores personal details for a trainer.
    """
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('PREFER_NOT_TO_SAY', 'Prefer not to say'),
    ]

    contact_number = models.CharField(max_length=15, primary_key=True)
    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    email = models.EmailField(unique=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    spoken_language = models.CharField(max_length=100, default='', blank=True)
    profile_photo = models.BinaryField(null=True, blank=True)
    profile_photo_mimetype = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'trainers_personal_details'
        verbose_name = "Trainer Personal Detail"
        verbose_name_plural = "Trainer Personal Details"

    def __str__(self):
        return f"{self.full_name} ({self.contact_number})"

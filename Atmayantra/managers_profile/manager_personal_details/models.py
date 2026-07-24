from django.db import models
from authapp.models import User


class ManagerPersonalDetails(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="manager_profile"
    )

    employee_name = models.CharField(max_length=200)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    employee_id = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=15)
    designation = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.TextField()
    date_of_joining = models.DateField()
    location = models.CharField(max_length=200)

    # ✅ BINARY STORAGE
    profile_photo = models.BinaryField(null=True, blank=True)
    profile_photo_mimetype = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.employee_name

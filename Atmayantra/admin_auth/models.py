from django.db import models

class AdminUser(models.Model):
    contact_number = models.CharField(max_length=15, primary_key=True)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)  # becomes True after OTP verification
    refresh_token = models.TextField(null=True, blank=True) # New field

    def __str__(self):
        return f"{self.name} ({self.contact_number})"

    class Meta:
        db_table = 'admin_user'  # optional: custom table name

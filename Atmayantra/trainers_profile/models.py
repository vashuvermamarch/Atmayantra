from django.db import models
from admin_auth.models import AdminUser


class TrainersPersonalDetails(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    approved_by = models.ForeignKey(
        AdminUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_trainers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.status}"

    class Meta:
        db_table = 'trainers_profile'


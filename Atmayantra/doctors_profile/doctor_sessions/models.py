from django.db import models
from django.conf import settings
import uuid


# =============================================================
# MODEL 1: Doctor Available Slots
# =============================================================
class DoctorAvailableSlot(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='available_slots',
        limit_choices_to={'user_type': 'Yoga Doctor'}
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'doctor_available_slots'
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date', 'start_time']

    def __str__(self):
        return f"{self.doctor.username} - {self.date} {self.start_time}"


# =============================================================
# MODEL 2: Session Booking
# =============================================================
class SessionBooking(models.Model):

    class SessionType(models.TextChoices):
        VIDEO_CALL = 'video_call', 'Video Call'
        CHAT = 'chat', 'Chat'
        VIDEO_CALL_CHAT = 'video_call_chat', 'Video Call + Chat'

    class BookingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='session_bookings'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_bookings'
    )
    slot = models.ForeignKey(
        DoctorAvailableSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )

    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        default=SessionType.VIDEO_CALL_CHAT
    )
    requirements = models.TextField(
        blank=True,
        default='',
        help_text="User ka problem ya requirement"
    )

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=800.00,
        help_text="Session fee in INR"
    )
    duration_minutes = models.IntegerField(
        default=30,
        help_text="Session duration in minutes"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'session_bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.doctor.username} ({self.status})"


# =============================================================
# MODEL 3: Payment (Demo)
# =============================================================
class Payment(models.Model):

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    booking = models.OneToOneField(
        SessionBooking,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    transaction_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.payment_status}"

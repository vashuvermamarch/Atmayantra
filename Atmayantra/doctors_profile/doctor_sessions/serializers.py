from rest_framework import serializers
from .models import DoctorAvailableSlot, SessionBooking, Payment


# =============================================================
# SLOT SERIALIZERS
# =============================================================
class DoctorAvailableSlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.username', read_only=True)

    class Meta:
        model = DoctorAvailableSlot
        fields = [
            'id', 'doctor', 'doctor_name',
            'date', 'start_time', 'end_time',
            'is_booked', 'created_at'
        ]
        read_only_fields = ['id', 'is_booked', 'created_at']


class AddSlotSerializer(serializers.Serializer):
    """Doctor adds multiple slots at once"""
    date = serializers.DateField()
    slots = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of {start_time, end_time}"
    )


# =============================================================
# BOOKING SERIALIZERS
# =============================================================
class SessionBookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionBooking
        fields = [
            'doctor', 'slot',
            'preferred_date', 'preferred_time',
            'session_type', 'requirements'
        ]


class SessionBookingListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    doctor_name = serializers.CharField(source='doctor.username', read_only=True)
    doctor_phone = serializers.CharField(source='doctor.phone_number', read_only=True)
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = SessionBooking
        fields = [
            'id', 'user', 'user_name', 'user_phone',
            'doctor', 'doctor_name', 'doctor_phone',
            'slot', 'preferred_date', 'preferred_time',
            'session_type', 'requirements', 'status',
            'amount', 'duration_minutes',
            'payment_status',
            'created_at', 'updated_at'
        ]

    def get_payment_status(self, obj):
        try:
            return obj.payment.payment_status
        except Payment.DoesNotExist:
            return None


# =============================================================
# PAYMENT SERIALIZERS
# =============================================================
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'amount',
            'payment_status', 'transaction_id',
            'paid_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'amount', 'payment_status',
            'transaction_id', 'paid_at', 'created_at'
        ]


class BookingSummarySerializer(serializers.ModelSerializer):
    """Booking summary with payment info - shown after doctor approval"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    doctor_name = serializers.CharField(source='doctor.username', read_only=True)
    doctor_phone = serializers.CharField(source='doctor.phone_number', read_only=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = SessionBooking
        fields = [
            'id', 'user_name',
            'doctor_name', 'doctor_phone',
            'preferred_date', 'preferred_time',
            'session_type', 'requirements',
            'status', 'amount', 'duration_minutes',
            'payment',
            'created_at', 'updated_at'
        ]

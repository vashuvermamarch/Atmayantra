from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone

from .models import DoctorAvailableSlot, SessionBooking, Payment
from .serializers import (
    DoctorAvailableSlotSerializer,
    AddSlotSerializer,
    SessionBookingCreateSerializer,
    SessionBookingListSerializer,
    BookingSummarySerializer,
    PaymentSerializer,
)
from authapp.models import User
from Atmayantra.utils import api_response

import logging
logger = logging.getLogger(__name__)


# =============================================================
# 1️⃣ ADD SLOTS — Doctor apne available slots add kare
# POST /api/doctors/sessions/add-slots/
# =============================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_slots(request):
    """
    Doctor adds available time slots.
    Body: { "date": "2026-04-10", "slots": [{"start_time": "10:00", "end_time": "10:30"}, ...] }
    """
    user = request.user

    if user.user_type != User.UserType.YOGA_DOCTOR:
        return api_response(False, "Only doctors can add slots.",
                            status_code=status.HTTP_403_FORBIDDEN)

    serializer = AddSlotSerializer(data=request.data)
    if not serializer.is_valid():
        return api_response(False, "Invalid data.", serializer.errors,
                            status_code=status.HTTP_400_BAD_REQUEST)

    date = serializer.validated_data['date']
    slots_data = serializer.validated_data['slots']
    created_slots = []

    for slot in slots_data:
        start_time = slot.get('start_time')
        end_time = slot.get('end_time')

        if not start_time or not end_time:
            continue

        # Duplicate check
        if DoctorAvailableSlot.objects.filter(
            doctor=user, date=date, start_time=start_time
        ).exists():
            continue

        obj = DoctorAvailableSlot.objects.create(
            doctor=user,
            date=date,
            start_time=start_time,
            end_time=end_time
        )
        created_slots.append(obj)

    serialized = DoctorAvailableSlotSerializer(created_slots, many=True)

    return api_response(True, f"{len(created_slots)} slot(s) added successfully.", {
        "total_added": len(created_slots),
        "slots": serialized.data
    }, status_code=status.HTTP_201_CREATED)


# =============================================================
# 2️⃣ GET AVAILABLE SLOTS — User doctor ke available slots dekhe
# GET /api/doctors/sessions/available-slots/<doctor_id>/
# =============================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_slots(request, doctor_id):
    """
    Get all available (non-booked) slots for a specific doctor.
    """
    try:
        doctor = User.objects.get(id=doctor_id, user_type='Yoga Doctor')
    except User.DoesNotExist:
        return api_response(False, "Doctor not found.",
                            status_code=status.HTTP_404_NOT_FOUND)

    slots = DoctorAvailableSlot.objects.filter(
        doctor=doctor,
        is_booked=False,
        date__gte=timezone.now().date()
    )

    serializer = DoctorAvailableSlotSerializer(slots, many=True)

    return api_response(True, "Available slots fetched.", {
        "doctor_name": doctor.username,
        "total_slots": slots.count(),
        "slots": serializer.data
    })


# =============================================================
# 3️⃣ BOOK SESSION — User booking request bheje
# POST /api/doctors/sessions/book/
# =============================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_session(request):
    """
    User creates a session booking request.
    Body: {
        "doctor": 5,
        "slot": 3,  (optional)
        "preferred_date": "2026-04-10",
        "preferred_time": "11:00",
        "session_type": "video_call_chat",
        "requirements": "Back pain problem..."
    }
    """
    user = request.user

    serializer = SessionBookingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return api_response(False, "Invalid booking data.", serializer.errors,
                            status_code=status.HTTP_400_BAD_REQUEST)

    doctor = serializer.validated_data['doctor']

    # Check doctor is valid
    if doctor.user_type != 'Yoga Doctor':
        return api_response(False, "Selected user is not a doctor.",
                            status_code=status.HTTP_400_BAD_REQUEST)

    # Check user is not booking with themselves
    if user.id == doctor.id:
        return api_response(False, "You cannot book a session with yourself.",
                            status_code=status.HTTP_400_BAD_REQUEST)

    # If slot is provided, mark it as booked
    slot = serializer.validated_data.get('slot')
    if slot:
        if slot.is_booked:
            return api_response(False, "This slot is already booked.",
                                status_code=status.HTTP_400_BAD_REQUEST)
        if slot.doctor != doctor:
            return api_response(False, "Slot does not belong to this doctor.",
                                status_code=status.HTTP_400_BAD_REQUEST)
        slot.is_booked = True
        slot.save()

    booking = SessionBooking.objects.create(
        user=user,
        doctor=doctor,
        slot=slot,
        preferred_date=serializer.validated_data['preferred_date'],
        preferred_time=serializer.validated_data['preferred_time'],
        session_type=serializer.validated_data.get('session_type', 'video_call_chat'),
        requirements=serializer.validated_data.get('requirements', ''),
        status='pending'
    )

    return api_response(True, "Session request sent to doctor. Waiting for approval.", {
        "booking_id": booking.id,
        "doctor_name": doctor.username,
        "preferred_date": str(booking.preferred_date),
        "preferred_time": str(booking.preferred_time),
        "session_type": booking.session_type,
        "status": booking.status
    }, status_code=status.HTTP_201_CREATED)


# =============================================================
# 4️⃣ MY BOOKINGS — User apni bookings dekhe
# GET /api/doctors/sessions/my-bookings/
# =============================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    """
    User sees all their session bookings.
    Optional query: ?status=pending / ?status=approved
    """
    user = request.user
    status_filter = request.GET.get('status')

    bookings = SessionBooking.objects.filter(user=user)

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    serializer = SessionBookingListSerializer(bookings, many=True)

    return api_response(True, "Your bookings fetched.", {
        "total": bookings.count(),
        "bookings": serializer.data
    })


# =============================================================
# 5️⃣ DOCTOR REQUESTS — Doctor apne pending requests dekhe
# GET /api/doctors/sessions/doctor-requests/
# =============================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_requests(request):
    """
    Doctor sees all session requests sent to them.
    Optional query: ?status=pending / ?status=approved
    """
    user = request.user

    if user.user_type != User.UserType.YOGA_DOCTOR:
        return api_response(False, "Only doctors can view requests.",
                            status_code=status.HTTP_403_FORBIDDEN)

    status_filter = request.GET.get('status')
    bookings = SessionBooking.objects.filter(doctor=user)

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    serializer = SessionBookingListSerializer(bookings, many=True)

    return api_response(True, "Session requests fetched.", {
        "total": bookings.count(),
        "requests": serializer.data
    })


# =============================================================
# 6️⃣ APPROVE BOOKING — Doctor booking approve kare
# POST /api/doctors/sessions/approve/<booking_id>/
# =============================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_booking(request, booking_id):
    """
    Doctor approves a session booking request.
    """
    user = request.user

    if user.user_type != User.UserType.YOGA_DOCTOR:
        return api_response(False, "Only doctors can approve bookings.",
                            status_code=status.HTTP_403_FORBIDDEN)

    try:
        booking = SessionBooking.objects.get(id=booking_id, doctor=user)
    except SessionBooking.DoesNotExist:
        return api_response(False, "Booking not found.",
                            status_code=status.HTTP_404_NOT_FOUND)

    if booking.status != 'pending':
        return api_response(False, f"Booking is already {booking.status}.",
                            status_code=status.HTTP_400_BAD_REQUEST)

    booking.status = 'approved'
    booking.save()

    return api_response(True, "Booking approved successfully!", {
        "booking_id": booking.id,
        "user_name": booking.user.username,
        "status": booking.status,
        "preferred_date": str(booking.preferred_date),
        "preferred_time": str(booking.preferred_time),
        "amount": str(booking.amount)
    })


# =============================================================
# 7️⃣ REJECT BOOKING — Doctor booking reject kare
# POST /api/doctors/sessions/reject/<booking_id>/
# =============================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_booking(request, booking_id):
    """
    Doctor rejects a session booking request.
    """
    user = request.user

    if user.user_type != User.UserType.YOGA_DOCTOR:
        return api_response(False, "Only doctors can reject bookings.",
                            status_code=status.HTTP_403_FORBIDDEN)

    try:
        booking = SessionBooking.objects.get(id=booking_id, doctor=user)
    except SessionBooking.DoesNotExist:
        return api_response(False, "Booking not found.",
                            status_code=status.HTTP_404_NOT_FOUND)

    if booking.status != 'pending':
        return api_response(False, f"Booking is already {booking.status}.",
                            status_code=status.HTTP_400_BAD_REQUEST)

    # If slot was booked, free it
    if booking.slot:
        booking.slot.is_booked = False
        booking.slot.save()

    booking.status = 'rejected'
    booking.save()

    return api_response(True, "Booking rejected.", {
        "booking_id": booking.id,
        "user_name": booking.user.username,
        "status": booking.status
    })


# =============================================================
# 8️⃣ CANCEL BOOKING — User booking cancel kare
# POST /api/doctors/sessions/cancel/<booking_id>/
# =============================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    """
    User cancels their own booking request.
    """
    user = request.user

    try:
        booking = SessionBooking.objects.get(id=booking_id, user=user)
    except SessionBooking.DoesNotExist:
        return api_response(False, "Booking not found.",
                            status_code=status.HTTP_404_NOT_FOUND)

    if booking.status in ['completed', 'cancelled']:
        return api_response(False, f"Cannot cancel. Booking is already {booking.status}.",
                            status_code=status.HTTP_400_BAD_REQUEST)

    # If slot was booked, free it
    if booking.slot:
        booking.slot.is_booked = False
        booking.slot.save()

    booking.status = 'cancelled'
    booking.save()

    return api_response(True, "Booking cancelled successfully.", {
        "booking_id": booking.id,
        "status": booking.status
    })


# =============================================================
# 9️⃣ BOOKING SUMMARY — Booking summary after approval
# GET /api/doctors/sessions/booking-summary/<booking_id>/
# =============================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_summary(request, booking_id):
    """
    Get full booking summary with payment info.
    Shown after doctor approves the request.
    """
    user = request.user

    try:
        booking = SessionBooking.objects.get(
            id=booking_id
        )
    except SessionBooking.DoesNotExist:
        return api_response(False, "Booking not found.",
                            status_code=status.HTTP_404_NOT_FOUND)

    # Only the user or doctor can view the summary
    if user.id != booking.user.id and user.id != booking.doctor.id:
        return api_response(False, "You don't have permission to view this booking.",
                            status_code=status.HTTP_403_FORBIDDEN)

    serializer = BookingSummarySerializer(booking)

    return api_response(True, "Booking summary fetched.", serializer.data)


# =============================================================
# 🔟 PAY — Demo payment
# POST /api/doctors/sessions/pay/<booking_id>/
# =============================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_for_session(request, booking_id):
    """
    Demo payment for a session booking.
    Only works if booking is approved.
    Body (demo - not really used): {
        "card_number": "4242424242424242",
        "expiry": "12/28",
        "cvv": "123"
    }
    """
    user = request.user

    try:
        booking = SessionBooking.objects.get(id=booking_id, user=user)
    except SessionBooking.DoesNotExist:
        return api_response(False, "Booking not found.",
                            status_code=status.HTTP_404_NOT_FOUND)

    if booking.status != 'approved':
        return api_response(False, "Booking must be approved before payment.",
                            status_code=status.HTTP_400_BAD_REQUEST)

    # Check if already paid
    if hasattr(booking, 'payment') and booking.payment.payment_status == 'success':
        return api_response(False, "Payment already completed.",
                            status_code=status.HTTP_400_BAD_REQUEST)

    # Create demo payment (always success)
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'amount': booking.amount,
            'payment_status': 'success',
            'paid_at': timezone.now()
        }
    )

    if not created:
        payment.payment_status = 'success'
        payment.paid_at = timezone.now()
        payment.save()

    # Update booking status to completed
    booking.status = 'completed'
    booking.save()

    serializer = PaymentSerializer(payment)

    return api_response(True, "Payment successful! Session booked.", {
        "payment": serializer.data,
        "booking_id": booking.id,
        "doctor_name": booking.doctor.username,
        "session_type": booking.session_type,
        "preferred_date": str(booking.preferred_date),
        "preferred_time": str(booking.preferred_time),
        "message": "You can now join the Video Call or Chat session."
    })

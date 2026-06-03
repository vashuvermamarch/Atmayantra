from django.urls import path
from . import views

urlpatterns = [
    # 1. Doctor adds available slots
    path('add-slots/', views.add_slots, name='add-slots'),

    # 2. Get available slots for a doctor
    path('available-slots/<int:doctor_id>/', views.get_available_slots, name='available-slots'),

    # 3. User creates booking request
    path('book/', views.book_session, name='book-session'),

    # 4. User sees their bookings
    path('my-bookings/', views.my_bookings, name='my-bookings'),

    # 5. Doctor sees pending requests
    path('doctor-requests/', views.doctor_requests, name='doctor-requests'),

    # 6. Doctor approves booking
    path('approve/<int:booking_id>/', views.approve_booking, name='approve-booking'),

    # 7. Doctor rejects booking
    path('reject/<int:booking_id>/', views.reject_booking, name='reject-booking'),

    # 8. User cancels booking
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel-booking'),

    # 9. Booking summary (after approval)
    path('booking-summary/<int:booking_id>/', views.booking_summary, name='booking-summary'),

    # 10. Demo payment
    path('pay/<int:booking_id>/', views.pay_for_session, name='pay-session'),
]

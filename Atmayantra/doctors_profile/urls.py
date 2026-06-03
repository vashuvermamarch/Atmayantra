from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.get_pending_doctors, name='doctor-list'),
    path('approve/<int:doctor_id>/', views.approve_doctor, name='doctor-approve'),
    path('reject/<int:doctor_id>/', views.reject_doctor, name='doctor-reject'),
]

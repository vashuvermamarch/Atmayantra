from django.urls import path

from . import views

urlpatterns = [
    path('', views.manage_bank_details, name='physio_bank_details'),
    path('qr-code/', views.view_bank_qr_code, name='physio_bank_qr_code'),
]

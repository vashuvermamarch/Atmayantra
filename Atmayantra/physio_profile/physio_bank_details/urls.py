from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_bank_details, name='physio_bank_details'),
]

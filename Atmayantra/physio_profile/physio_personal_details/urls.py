from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_personal_details, name='physio_personal_details'),
]

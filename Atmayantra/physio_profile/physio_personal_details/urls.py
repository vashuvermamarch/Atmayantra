from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_personal_details, name='physio_personal_details'),
    path('profile-photo/', views.view_profile_photo, name='physio_profile_photo'),
]

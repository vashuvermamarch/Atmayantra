from django.urls import path
from .views import (
    DoctorPersonalDetailsView,
    ProfilePhotoViewerView,
    DoctorProfilePhotoDownloadView,
    DoctorProfilePhotoView
)

urlpatterns = [
    # Endpoint for creating a new record (POST)
    path('', DoctorPersonalDetailsView.as_view(), name='doctor-personal-details-create'),
    
    # Endpoint for getting all records (GET)
    path('all/', DoctorPersonalDetailsView.as_view(), name='doctor-personal-details-all'),

    # Endpoint for creating the profile photo (POST)
    path('photo/', DoctorProfilePhotoView.as_view(), name='doctor-profile-photo-manage'),
    path('photo/<str:contact_number>/', DoctorProfilePhotoView.as_view(), name='doctor-profile-photo-update'),

    # Endpoint for GET/PUT/PATCH/DELETE for a specific doctor (should be after specific paths)
    path('<str:contact_number>/', DoctorPersonalDetailsView.as_view(), name='doctor-personal-details-detail'),

    # Endpoint for displaying the profile photo
    path('<str:contact_number>/photo/view/', ProfilePhotoViewerView.as_view(), name='doctor-profile-photo-view'),

    # Endpoint for downloading the profile photo
    path('<str:contact_number>/photo/download/', DoctorProfilePhotoDownloadView.as_view(), name='doctor-profile-photo-download'),
]

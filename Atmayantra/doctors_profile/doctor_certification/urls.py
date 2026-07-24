from django.urls import path
from .views import (
    DoctorCertificationView,
    GraduationCertificateDownloadView,
    ExperienceLetterDownloadView,
    ResumeCvDownloadView,
    LicenseDownloadView
)

urlpatterns = [
    # Endpoint for creating a new certification record (POST)
    path('', DoctorCertificationView.as_view(), name='doctor-certification-create'),

    # Endpoint for GET, PUT, PATCH, DELETE for a specific doctor's certification
    path('<str:contact_number>/', DoctorCertificationView.as_view(), name='doctor-certification-detail'),

    # Endpoints for downloading files
    path('<str:contact_number>/graduation-certificate/download/', GraduationCertificateDownloadView.as_view(), name='download-graduation-certificate'),
    path('<str:contact_number>/experience-letter/download/', ExperienceLetterDownloadView.as_view(), name='download-experience-letter'),
    path('<str:contact_number>/resume-cv/download/', ResumeCvDownloadView.as_view(), name='download-resume-cv'),
    path('<str:contact_number>/license-pdf/download/', LicenseDownloadView.as_view(), name='download-license-pdf'),
]
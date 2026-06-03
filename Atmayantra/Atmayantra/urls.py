"""
URL configuration for Atmayantra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include([
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('admin-auth/', include('admin_auth.urls')),
        path('auth/', include('authapp.urls')),
        path('trainers/profile/', include('trainers_profile.urls')),
        path('doctors/details/', include('doctors_profile.doctor_personal_details.urls')),
        path('doctors/certifications/', include('doctors_profile.doctor_certification.urls')),
        path('doctors/documents/', include('doctors_profile.doctor_documents.urls')),
        path('doctors/bank-details/', include('doctors_profile.doctor_bank_details.urls')),
        path('doctors/profile/', include('doctors_profile.urls')),
        path('doctors/sessions/', include('doctors_profile.doctor_sessions.urls')),
        path('trainers/personal-details/', include('trainers_profile.trainers_personal_detials.urls')),
        path('trainers/certifications/', include('trainers_profile.trainers_certifications.urls')),
        path('trainers/documents/', include('trainers_profile.trainers_documents.urls')),
        path('trainers/bank-details/', include('trainers_profile.trainers_bank_details.urls')),
        path('managers/personal-details/', include('managers_profile.manager_personal_details.urls')),
        path('managers/documents/', include('managers_profile.manager_documents.urls')),
        path('managers/bank-details/', include('managers_profile.manager_bank_details.urls')),
        # Add here me
        path('physio/profile/', include('physio_profile.urls')),
        path('physio/personal-details/', include('physio_profile.physio_personal_details.urls')),
        path('physio/certifications/', include('physio_profile.physio_certifications.urls')),
        path('physio/documents/', include('physio_profile.physio_documents.urls')),
        path('physio/bank-details/', include('physio_profile.physio_bank_details.urls')),
    ]))
]

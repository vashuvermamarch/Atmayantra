from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorCertificationViewSet

router = DefaultRouter()
router.register(r'certifications', DoctorCertificationViewSet, basename='certification')

urlpatterns = [
    path('', include(router.urls)),
]
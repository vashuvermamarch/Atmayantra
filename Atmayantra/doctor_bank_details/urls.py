from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorBankDetailsViewSet

router = DefaultRouter()
router.register(r'', DoctorBankDetailsViewSet, basename='doctor-bank')

urlpatterns = [
    path('', include(router.urls)),
]

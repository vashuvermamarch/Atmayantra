from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorPersonalDetailsViewSet

router = DefaultRouter()
router.register(r'doctors', DoctorPersonalDetailsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
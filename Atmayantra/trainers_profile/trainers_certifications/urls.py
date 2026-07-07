from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TrainerCertificationViewSet

router = DefaultRouter()
router.register(r'', TrainerCertificationViewSet, basename='trainer-certification')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]

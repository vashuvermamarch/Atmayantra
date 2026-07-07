from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TrainerPersonalDetailViewSet

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'', TrainerPersonalDetailViewSet, basename='trainer-personal-detail') # The lookup is now handled by the viewset

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]

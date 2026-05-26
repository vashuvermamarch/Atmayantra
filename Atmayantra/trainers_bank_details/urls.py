from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TrainerBankDetailsViewSet

router = DefaultRouter()
router.register(r'', TrainerBankDetailsViewSet, basename='trainer-bank-details')

urlpatterns = [
    path('', include(router.urls)),
]


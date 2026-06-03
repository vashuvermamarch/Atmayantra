from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrainerBankDetailsViewSet

router = DefaultRouter()
router.register(r'', TrainerBankDetailsViewSet, basename='trainer-bank-details')

urlpatterns = [
    path('', include(router.urls)),
]


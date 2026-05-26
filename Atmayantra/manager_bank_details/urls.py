from django.urls import path

from .views import ManagerBankUpdateDeleteView, ManagerBankView

urlpatterns = [
    path('all/', ManagerBankView.as_view()),
    path('<str:contact_number>/', ManagerBankView.as_view()),
    path('edit/<str:contact_number>/', ManagerBankUpdateDeleteView.as_view()),
]

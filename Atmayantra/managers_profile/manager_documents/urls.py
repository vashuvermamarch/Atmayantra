from django.urls import path
from .views import ManagerDocsView, ManagerDocControlView

urlpatterns = [
    path('all/', ManagerDocsView.as_view()),
    path('<str:contact_number>/', ManagerDocsView.as_view()),
    path('<str:contact_number>/<int:doc_id>/', ManagerDocControlView.as_view()),
]

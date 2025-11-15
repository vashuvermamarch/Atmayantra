from django.urls import path
from .views import DoctorDocumentView, DoctorDocumentDownloadView

urlpatterns = [
    path('', DoctorDocumentView.as_view(), name='document-create'),
    path('<str:contact_number>/', DoctorDocumentView.as_view(), name='document-list'),
    path('<str:contact_number>/<str:document_id>/', DoctorDocumentView.as_view(), name='document-detail'),
    path('<str:contact_number>/<str:document_id>/download/', DoctorDocumentDownloadView.as_view(), name='document-download'),
]
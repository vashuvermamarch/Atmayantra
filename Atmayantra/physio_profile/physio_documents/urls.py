from django.urls import path

from . import views

urlpatterns = [
    path('', views.manage_documentation, name='physio_documents'),
    path('<str:field_name>/', views.view_document_file, name='physio_document_file'),
]

from django.urls import path
from .views import TrainerDocumentViewSet

urlpatterns = [
    # POST: Create a document (trainer in payload)
    # GET: List all documents for all trainers
    path('', TrainerDocumentViewSet.as_view({'post': 'create', 'get': 'list'}), name='trainer-document-list-create'),
    
    # GET: List all documents for a specific trainer
    path('<str:contact_number>/', TrainerDocumentViewSet.as_view({'get': 'list'}), name='trainer-document-list-by-trainer'),
    
    # GET, PUT, PATCH, DELETE: Manage a specific document
    path('<str:contact_number>/<int:pk>/', TrainerDocumentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='trainer-document-detail'),
    
    # GET: View or download a specific document
    path('<str:contact_number>/<int:pk>/view/', TrainerDocumentViewSet.as_view({'get': 'view'}), name='trainer-document-view'),
    path('<str:contact_number>/<int:pk>/download/', TrainerDocumentViewSet.as_view({'get': 'download'}), name='trainer-document-download'),
]
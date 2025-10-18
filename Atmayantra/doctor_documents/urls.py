from django.urls import path
from .views import DoctorDocumentViewSet

urlpatterns = [
    path('documents/create/', DoctorDocumentViewSet.as_view({'post': 'create'}), name='document-create'),
    path('documents/<str:contact_number>/', DoctorDocumentViewSet.as_view({'get': 'list'}), name='document-list'),
    path('documents/<str:contact_number>/<int:pk>/', DoctorDocumentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='document-detail'),
    path('documents/<str:contact_number>/<int:pk>/file/', DoctorDocumentViewSet.as_view({'get': 'file'}), name='document-file'),
]
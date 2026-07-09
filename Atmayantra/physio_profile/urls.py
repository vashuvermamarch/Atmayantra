from django.urls import path

from . import views

urlpatterns = [
    # Admin Review APIs
    path('list/', views.get_pending_physios, name='physio-list'),
    path('approve/<int:physio_id>/', views.approve_physio, name='physio-approve'),
    path('reject/<int:physio_id>/', views.reject_physio, name='physio-reject'),
]

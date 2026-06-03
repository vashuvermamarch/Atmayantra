from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.get_all_trainers, name='trainer-list'),
    path('approve/<int:trainer_id>/', views.approve_trainer, name='approve-trainer'),
    path('reject/<int:trainer_id>/', views.reject_trainer, name='reject-trainer'),
]


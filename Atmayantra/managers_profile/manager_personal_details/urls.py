from django.urls import path

from .views import ManagerPersonalView, ManagerPhotoDownloadView, ManagerPhotoView, ManagerUpdateDeleteView

urlpatterns = [
    path('all/', ManagerPersonalView.as_view()),
    path('<str:contact_number>/', ManagerPersonalView.as_view()),

    path('photo/view/<str:contact_number>/', ManagerPhotoView.as_view()),
    path('photo/download/<str:contact_number>/', ManagerPhotoDownloadView.as_view()),

    path('edit/<str:contact_number>/', ManagerUpdateDeleteView.as_view()),
]

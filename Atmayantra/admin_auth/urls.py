from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup),
    path('verify-signup/', views.verify_signup),
    path('login-request/', views.login_request),
    path('verify-login/', views.verify_login_otp),
    path('refresh-token/', views.refresh_token),
    path('decode-token/', views.decode_token),
]

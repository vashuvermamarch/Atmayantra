from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('verify-signup/', views.verify_signup, name='verify_signup'),
    path('login/', views.login_request, name='login_request'),
    path('verify-login/', views.verify_login_otp, name='verify_login_otp'),
    path('decode-token/', views.decode_token, name='decode_token'),
]

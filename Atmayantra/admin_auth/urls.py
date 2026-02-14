from django.urls import path
from . import views

urlpatterns = [
    path('admin-signup/', views.signup, name='admin-signup'),
    path('admin-verify-signup/', views.verify_signup),
    path('admin-login/', views.login_request),
    path('admin-verify-login/', views.verify_login_otp),
    path('admin-refresh-token/', views.refresh_token),
    path('admin-decode-token/', views.decode_token),
    path('admin-logout/', views.logout),
    path('admin-resend-signup-otp/', views.resend_signup_otp),
    path('admin-resend-login-otp/', views.resend_login_otp),
    path('admin-resend-reset-password-otp/', views.resend_reset_password_otp),
    path('admin-forgot-password/', views.forgot_password_request),
    path('admin-verify-reset-otp/', views.verify_reset_otp),
    path('admin-reset-password/', views.reset_password),
    path('manager/step1/', views.manager_step1_personal),
    path('manager/step2/<int:temp_id>/', views.manager_step2_documents),
    path('manager/step3/<int:temp_id>/', views.manager_step3_finalize),
]

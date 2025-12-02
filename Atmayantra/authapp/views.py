from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.conf import settings

from .serializers import UserSerializer
from .models import User, UserRefreshToken, SignupRefreshToken

from random import randint
from rest_framework_simplejwt.tokens import RefreshToken
from Atmayantra.utils import api_response

import logging
import jwt
from datetime import datetime

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer

    # 1) SIGNUP → send OTP
    @action(detail=False, methods=['post'])
    def signup(self, request):
        serializer = UserSerializer(data=request.data)

        if not serializer.is_valid():
            return api_response(False, "Invalid data provided.",
                                serializer.errors, status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        username = serializer.validated_data['username']
        email = serializer.validated_data.get('email')

        # Unique validations
        if User.objects.filter(phone_number=phone_number).exists():
            return api_response(False, "Phone number already exists.", status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return api_response(False, "Username already exists.", status.HTTP_400_BAD_REQUEST)
        if email and User.objects.filter(email=email).exists():
            return api_response(False, "Email already exists.", status.HTTP_400_BAD_REQUEST)

        otp = str(randint(100000, 999999))

        cache.set(
            f'otp_signup_{phone_number}',
            {"otp": otp, "data": serializer.validated_data},
            timeout=300
        )

        print(f"OTP for signup ({phone_number}): {otp}")

        return api_response(True, "OTP sent successfully.",
                            {"phone_number": phone_number, "otp": otp})

    # 2) VERIFY SIGNUP → create user + tokens
    @action(detail=False, methods=['post'])
    def verify_signup(self, request):
        phone_number = request.data.get("phone_number")
        otp = request.data.get("otp")

        stored = cache.get(f'otp_signup_{phone_number}')

        if not stored or stored["otp"] != otp:
            return api_response(False, "Invalid or expired OTP.", status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=stored["data"])
        if not serializer.is_valid():
            return api_response(False, "Error creating user.",
                                serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = serializer.save(is_verified=True)

        # USER types auto-active
        if user.user_type != User.UserType.USER:
            user.is_active = False  # Needs admin approval
        user.save()

        cache.delete(f'otp_signup_{phone_number}')

        # SIGNUP TOKEN (no expiry)
        signup_payload = {
            "username": user.username,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "iat": datetime.utcnow()
        }
        signup_token = jwt.encode(signup_payload, settings.SECRET_KEY, algorithm="HS256")

        # SIGNUP REFRESH TOKEN
        signup_refresh_payload = {
            "username": user.username,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "type": "signup_refresh",
            "iat": datetime.utcnow()
        }
        signup_refresh_token = jwt.encode(signup_refresh_payload, settings.SECRET_KEY, algorithm="HS256")

        SignupRefreshToken.objects.create(user=user, token=signup_refresh_token)

        return api_response(
            True,
            "Signup verified successfully.",
            {
                "user": {
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "user_type": user.user_type,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified
                },
                "signup_token": signup_token,
                "signup_refresh_token": signup_refresh_token
            },
            status.HTTP_201_CREATED
        )

    # 3) REFRESH SIGNUP TOKEN → using signup_refresh_token
    @action(detail=False, methods=['post'])
    def refresh_signup_token(self, request):
        signup_refresh_token = request.data.get("signup_refresh_token")

        if not signup_refresh_token:
            return api_response(False, "signup_refresh_token required.",
                                status.HTTP_400_BAD_REQUEST)

        try:
            saved = SignupRefreshToken.objects.get(token=signup_refresh_token)
        except SignupRefreshToken.DoesNotExist:
            return api_response(False, "Invalid signup_refresh_token.",
                                status.HTTP_400_BAD_REQUEST)

        user = saved.user

        new_signup_payload = {
            "username": user.username,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "iat": datetime.utcnow()
        }

        new_signup_token = jwt.encode(new_signup_payload, settings.SECRET_KEY, algorithm="HS256")

        return api_response(True, "New signup token generated.",
                            {"signup_token": new_signup_token})

    # 4) LOGIN → username + password + signup_token
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        signup_token = request.data.get("signup_token")

        if not username or not password or not signup_token:
            return api_response(False, "All fields required.", status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return api_response(False, "User not found.", status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return api_response(False, "Invalid password.", status.HTTP_400_BAD_REQUEST)

        try:
            decoded = jwt.decode(signup_token, settings.SECRET_KEY, algorithms=["HS256"])
        except:
            return api_response(False, "Invalid signup token.", status.HTTP_400_BAD_REQUEST)

        if decoded["username"] != user.username or decoded["phone_number"] != user.phone_number:
            return api_response(False, "Signup token mismatch.", status.HTTP_400_BAD_REQUEST)

        if not user.is_verified:
            return api_response(False, "User not verified.", status.HTTP_403_FORBIDDEN)

        if not user.is_active:
            return api_response(False, "User not active (admin approval pending).",
                                status.HTTP_403_FORBIDDEN)

        # GENERATE LOGIN TOKENS
        refresh = RefreshToken.for_user(user)
        UserRefreshToken.objects.create(user=user, refresh_token=str(refresh))

        return api_response(True, "Login successful.",
                            {"refresh": str(refresh), "access": str(refresh.access_token)})

    # 5) LOGOUT → delete refresh token
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get("refresh")

        try:
            UserRefreshToken.objects.get(user=request.user,
                                         refresh_token=refresh_token).delete()
            return api_response(True, "Logged out successfully.")
        except UserRefreshToken.DoesNotExist:
            return api_response(False, "Invalid refresh token.", status.HTTP_400_BAD_REQUEST)

    # 6) Protected View → FULL USER DETAILS
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def protected_view(self, request):
        user = request.user

        data = {
            "username": user.username,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }

        return api_response(True, "Authenticated user details.", data)

    # 7) Public lookup based on phone number
    @action(detail=False, methods=['get'], url_path=r'user-data/(?P<phone_number>[^/.]+)')
    def user_data(self, request, phone_number=None):
        try:
            user = User.objects.get(phone_number=phone_number)

            data = {
                "username": user.username,
                "phone_number": user.phone_number,
                "user_type": user.user_type,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            }

            return api_response(True, "User found", data)

        except User.DoesNotExist:
            return api_response(False, "User not found", status.HTTP_404_NOT_FOUND)

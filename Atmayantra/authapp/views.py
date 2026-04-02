from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.conf import settings

from .serializers import UserSerializer
from .models import User, UserRefreshToken, SignupRefreshToken

from random import randint
from Atmayantra.utils import api_response

import logging
import jwt
from datetime import datetime, timedelta

# ✅ USE CUSTOM TOKEN
from .custom_tokens import CustomRefreshToken

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer

    # ------------------------------------------------------------
    # 1️⃣ SIGNUP → SEND OTP
    # ------------------------------------------------------------
    @action(detail=False, methods=['post'])
    def signup(self, request):
        serializer = UserSerializer(data=request.data)

        if not serializer.is_valid():
            return api_response(False, "Invalid data provided.",
                                serializer.errors, status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        username = serializer.validated_data['username']
        email = serializer.validated_data.get('email')

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

        return api_response(True, "OTP sent successfully.", {
            "phone_number": phone_number,
            "otp": otp
        }, status.HTTP_200_OK)

    # ------------------------------------------------------------
    # 2️⃣ VERIFY SIGNUP → CREATE USER
    # ------------------------------------------------------------
    @action(detail=False, methods=['post'])
    def verify_signup(self, request):
        phone_number = request.data.get("phone_number")
        otp = request.data.get("otp")

        stored = cache.get(f'otp_signup_{phone_number}')

        if not stored or stored["otp"] != otp:
            return api_response(False, "Invalid or expired OTP.", status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=stored["data"])
        if not serializer.is_valid():
            return api_response(False, "Error creating user.", serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = serializer.save(is_verified=True)

        if user.user_type != User.UserType.USER:
            user.is_active = False
        user.save()

        cache.delete(f'otp_signup_{phone_number}')

        # Signup Tokens
        signup_payload = {
            "username": user.username,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=settings.SIGNUP_TOKEN_LIFETIME_MINUTES)
        }

        signup_token = jwt.encode(signup_payload, settings.SECRET_KEY, algorithm="HS256")

        signup_refresh_payload = {
            "username": user.username,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "type": "signup_refresh",
            "iat": datetime.utcnow()
        }

        signup_refresh_token = jwt.encode(signup_refresh_payload, settings.SECRET_KEY, algorithm="HS256")

        SignupRefreshToken.objects.create(user=user, token=signup_refresh_token)

        return api_response(True, "Signup verified successfully.", {
            "user": {
                "username": user.username,
                "phone_number": user.phone_number,
                "user_type": user.user_type,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            },
            "signup_token": signup_token,
            "signup_refresh_token": signup_refresh_token
        }, status.HTTP_200_OK)

    # ------------------------------------------------------------
    # 3️⃣ LOGIN REQUEST (Step 1: Credentials Check + OTP Generation)
    # ------------------------------------------------------------
    @action(detail=False, methods=['post'])
    def login_request(self, request):
        username = request.data.get("username")
        phone_number = request.data.get("phone_number")
        password = request.data.get("password")
        signup_token = request.data.get("signup_token")

        if not password:
            return api_response(False, "Password is required.", status.HTTP_400_BAD_REQUEST)

        # 1. IDENTIFY USER
        if username:
            # Manager Case
            try:
                user = User.objects.get(username=username)
                if user.user_type != User.UserType.MANAGER:
                    return api_response(False, "Unauthorized user type. Managers must use username, others must use phone number.", status.HTTP_403_FORBIDDEN)
            except User.DoesNotExist:
                return api_response(False, "Manager not found with this username.", status.HTTP_404_NOT_FOUND)
            id_key = username
        elif phone_number:
            # Doctor/Trainer Case
            if not signup_token:
                return api_response(False, "signup_token is required for this role.", status.HTTP_400_BAD_REQUEST)
            try:
                user = User.objects.get(phone_number=phone_number)
                if user.user_type == User.UserType.MANAGER:
                    return api_response(False, "Managers must log in with their username.", status.HTTP_403_FORBIDDEN)
                
                # Verify signup_token
                try:
                    decoded = jwt.decode(signup_token, settings.SECRET_KEY, algorithms=["HS256"])
                    if decoded.get("phone_number") != user.phone_number:
                        return api_response(False, "Signup token does not match this account.", status.HTTP_403_FORBIDDEN)
                except jwt.ExpiredSignatureError:
                    return api_response(False, "Signup token has expired. Please refresh it.", status.HTTP_403_FORBIDDEN)
                except:
                    return api_response(False, "Invalid signup token.", status.HTTP_403_FORBIDDEN)
                    
            except User.DoesNotExist:
                return api_response(False, "User not found with this phone number.", status.HTTP_404_NOT_FOUND)
            id_key = phone_number
        else:
            return api_response(False, "Identification (username or phone_number) required.", status.HTTP_400_BAD_REQUEST)

        # 2. CHECK PASSWORD
        if not user.check_password(password):
            return api_response(False, "Invalid password.", status.HTTP_400_BAD_REQUEST)

        # 3. VERIFICATION CHECKS
        if not user.is_verified:
            return api_response(False, "Account not verified.", status.HTTP_403_FORBIDDEN)
        if not user.is_active:
            return api_response(False, "Account not active. Please wait for admin approval.", status.HTTP_403_FORBIDDEN)

        # 4. GENERATE OTP
        otp = str(randint(100000, 999999))
        cache.set(f'otp_login_{id_key}', otp, timeout=300)

        return api_response(True, "Login OTP sent successfully.", {
            "id_key": id_key,
            "otp": otp # For development/testing
        }, status.HTTP_200_OK)

    # ------------------------------------------------------------
    # 4️⃣ VERIFY LOGIN (Step 2: OTP Verification + Token Issuance)
    # ------------------------------------------------------------
    @action(detail=False, methods=['post'])
    def verify_login(self, request):
        username = request.data.get("username")
        phone_number = request.data.get("phone_number")
        otp = request.data.get("otp")

        # Determine which identifier was used
        id_key = username if username else phone_number

        if not id_key or not otp:
            return api_response(False, "Identification and OTP are required.", status.HTTP_400_BAD_REQUEST)

        stored_otp = cache.get(f'otp_login_{id_key}')
        if not stored_otp or stored_otp != otp:
            return api_response(False, "Invalid or expired OTP.", status.HTTP_400_BAD_REQUEST)

        try:
            if username:
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return api_response(False, "User accounts could not be verified.", status.HTTP_404_NOT_FOUND)

        # Clean Up
        cache.delete(f'otp_login_{id_key}')

        # Issue Tokens
        refresh = CustomRefreshToken.for_user(user)
        UserRefreshToken.objects.create(
            user=user,
            refresh_token=str(refresh)
        )

        return api_response(True, "Login successful.", {
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }, status.HTTP_200_OK)

    # ------------------------------------------------------------
    # 4️⃣ LOGOUT
    # ------------------------------------------------------------
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):

        refresh_token = request.data.get("refresh")

        try:
            UserRefreshToken.objects.get(
                user=request.user,
                refresh_token=refresh_token
            ).delete()

            return api_response(True, "Logged out successfully.", status_code=status.HTTP_200_OK)

        except UserRefreshToken.DoesNotExist:
            return api_response(False, "Invalid refresh token.", status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------
    # 5️⃣ PROTECTED VIEW
    # ------------------------------------------------------------
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def protected_view(self, request):

        user = request.user

        return api_response(True, "Authenticated user.", {
            "username": user.username,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }, status.HTTP_200_OK)

    # ------------------------------------------------------------
    # 6️⃣ PUBLIC USER LOOKUP
    # ------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path=r'user-data/(?P<phone_number>[^/.]+)')
    def user_data(self, request, phone_number=None):

        try:
            user = User.objects.get(phone_number=phone_number)

            return api_response(True, "User found", {
                "username": user.username,
                "phone_number": user.phone_number,
                "user_type": user.user_type,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            }, status.HTTP_200_OK)

        except User.DoesNotExist:
            return api_response(False, "User not found", status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------
    # 7️⃣ REFRESH SIGNUP TOKEN
    # ------------------------------------------------------------
    @action(detail=False, methods=['post'])
    def refresh_signup_token(self, request):
        """
        Refreshes a short-lived signup_token using a signup_refresh_token.
        """
        refresh_token = request.data.get("signup_refresh_token")

        if not refresh_token:
            return api_response(False, "signup_refresh_token is required.", status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Verify existence in DB
            stored_refresh = SignupRefreshToken.objects.get(token=refresh_token)
            user = stored_refresh.user

            # 2. Decode and verify the refresh token itself
            decoded = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
            
            if decoded.get("type") != "signup_refresh":
                return api_response(False, "Invalid token type.", status.HTTP_400_BAD_REQUEST)

            # 3. Generate a new short-lived signup_token
            new_signup_payload = {
                "username": user.username,
                "phone_number": user.phone_number,
                "user_type": user.user_type,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=settings.SIGNUP_TOKEN_LIFETIME_MINUTES)
            }
            new_signup_token = jwt.encode(new_signup_payload, settings.SECRET_KEY, algorithm="HS256")

            return api_response(True, "Signup token refreshed successfully.", {
                "signup_token": new_signup_token
            }, status.HTTP_200_OK)

        except SignupRefreshToken.DoesNotExist:
            return api_response(False, "Refresh token not found or already used.", status.HTTP_401_UNAUTHORIZED)
        except jwt.ExpiredSignatureError:
            return api_response(False, "Signup refresh token has expired. Please signup again.", status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return api_response(False, "Invalid signup refresh token.", status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Error in refresh_signup_token: {str(e)}")
            return api_response(False, "An unexpected error occurred.", status.HTTP_500_INTERNAL_SERVER_ERROR)

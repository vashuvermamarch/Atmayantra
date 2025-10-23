from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from .serializers import UserSerializer
from .models import User
from random import randint
from rest_framework_simplejwt.tokens import RefreshToken
from Atmayantra.utils import api_response
import logging

logger = logging.getLogger(__name__)

class AuthViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'])
    def signup(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            if User.objects.filter(phone_number=phone_number).exists() or \
               User.objects.filter(email=serializer.validated_data['email']).exists() or \
               User.objects.filter(username=serializer.validated_data['username']).exists():
                return api_response(False, "User with given phone number, email, or username already exists.", status_code=status.HTTP_400_BAD_REQUEST)

            otp = str(randint(100000, 999999))
            cache.set(f'otp_{phone_number}', {
                'otp': otp,
                'data': serializer.validated_data
            }, timeout=300)  # OTP valid for 5 minutes

            print(f"OTP for signup ({phone_number}): {otp}")
            return api_response(True, f"OTP sent to your phone (simulated): {otp}")
        return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_signup(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        stored = cache.get(f'otp_{phone_number}')

        if not stored or stored['otp'] != otp:
            return api_response(False, "Invalid or expired OTP.", status_code=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=stored['data'])
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User created with ID: {user.id}")
            cache.delete(f'otp_{phone_number}')
            return api_response(True, "User registered successfully.", serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(False, "An error occurred during registration.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        phone_number = request.data.get('phone_number')
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        otp = str(randint(100000, 999999))
        cache.set(f'login_otp_{phone_number}', {
            'otp': otp,
            'user_id': user.id
        }, timeout=300)

        print(f"OTP for login ({phone_number}): {otp}")
        return api_response(True, f"OTP sent to your phone (simulated): {otp}")

    @action(detail=False, methods=['post'])
    def verify_login(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        stored = cache.get(f'login_otp_{phone_number}')

        if not stored or stored['otp'] != otp:
            return api_response(False, "Invalid or expired OTP.", status_code=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=stored['user_id'])
        refresh = RefreshToken.for_user(user)
        cache.delete(f'login_otp_{phone_number}')

        token_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return api_response(True, "Login successful.", token_data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def protected_view(self, request):
        user = request.user
        user_data = {
            "message": f"Hello, {user.username}! You are authorized.",
            "user_type": user.user_type
        }
        return api_response(True, "User is authenticated.", user_data)
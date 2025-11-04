from rest_framework.decorators import api_view, parser_classes
from .decorators import admin_login_required
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.conf import settings
from .models import AdminUser
import random
import jwt
import datetime


# -----------------------------------------------------------
# STEP 1: Signup Request
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def signup(request):
    contact_number = request.data.get('contact_number')
    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    if not all([contact_number, name, email, password, confirm_password]):
        return Response({'success': False, 'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({'success': False, 'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

    if AdminUser.objects.filter(contact_number=contact_number).exists():
        return Response({'success': False, 'error': 'Contact number already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    if AdminUser.objects.filter(email=email).exists():
        return Response({'success': False, 'error': 'Email already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    otp = str(random.randint(100000, 999999))
    cache.set(f"signup_otp_{contact_number}", {'otp': otp, 'data': {
        'contact_number': contact_number,
        'name': name,
        'email': email,
        'password': password
    }}, timeout=settings.OTP_EXPIRY_MINUTES * 60)

    return Response({'success': True, 'response':{
        'message': 'OTP generated successfully (valid for 15 minutes)',
        'otp': otp,
        'contact_number': contact_number,
        'email': email
    }}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 2: Verify Signup OTP
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def verify_signup(request):
    contact_number = request.data.get('contact_number')
    otp = request.data.get('otp')

    if not contact_number or not otp:
        return Response({'success': False, 'error': 'Contact number and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

    cached_data = cache.get(f"signup_otp_{contact_number}")
    if not cached_data:
        return Response({'success': False, 'error': 'OTP expired or not found.'}, status=status.HTTP_400_BAD_REQUEST)

    if cached_data['otp'] != otp:
        return Response({'success': False, 'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    data = cached_data['data']
    AdminUser.objects.create(
        contact_number=data['contact_number'],
        name=data['name'],
        email=data['email'],
        password=data['password']
    )
    cache.delete(f"signup_otp_{contact_number}")

    return Response({'success': True, 'response':{'message': 'Signup successful!'}}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 3: Login Request (Generate OTP)
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def login_request(request):
    contact_number = request.data.get('contact_number')
    password = request.data.get('password')

    if not contact_number or not password:
        return Response({'success': False, 'error': 'Contact number and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        admin_user = AdminUser.objects.get(contact_number=contact_number)
    except AdminUser.DoesNotExist:
        return Response({'success': False, 'error': 'Invalid contact number or password.'}, status=status.HTTP_400_BAD_REQUEST)

    if admin_user.password != password:
        return Response({'success': False, 'error': 'Invalid contact number or password.'}, status=status.HTTP_400_BAD_REQUEST)

    otp = str(random.randint(100000, 999999))
    cache.set(f"login_otp_{contact_number}", otp, timeout=settings.OTP_EXPIRY_MINUTES * 60)

    return Response({'success': True, 'response':{
        'message': 'Login OTP generated successfully (valid for 15 minutes)',
        'contact_number': admin_user.contact_number,
        'email': admin_user.email,
        'otp': otp
    }}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 4: Verify Login OTP → Return ACCESS + REFRESH Tokens
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def verify_login_otp(request):
    contact_number = request.data.get('contact_number')
    otp = request.data.get('otp')

    if not contact_number or not otp:
        return Response({'success': False, 'error': 'Contact number and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

    cached_otp = cache.get(f"login_otp_{contact_number}")
    if cached_otp is None:
        return Response({'success': False, 'error': 'OTP expired or not found.'}, status=status.HTTP_400_BAD_REQUEST)

    if cached_otp != otp:
        return Response({'success': False, 'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    cache.delete(f"login_otp_{contact_number}")

    # Get user and generate JWT tokens
    try:
        user = AdminUser.objects.get(contact_number=contact_number)
    except AdminUser.DoesNotExist:
        return Response({'success': False, 'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    access_payload = {
        'contact_number': user.contact_number,
        'name': user.name,
        'email': user.email,
        'type': 'access',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES)  # short lifespan
    }

    refresh_payload = {
        'contact_number': user.contact_number,
        'type': 'refresh',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)  # long lifespan
    }

    access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    user.refresh_token = refresh_token
    user.save()

    return Response({'success': True, 'response':{
        'message': 'Login successful!',
        'access_token': access_token,
        'refresh_token': refresh_token
    }}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 5: Refresh Access Token using Refresh Token
# -----------------------------------------------------------
@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return Response({'success': False, 'error': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        decoded = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if decoded.get('type') != 'refresh':
            return Response({'success': False, 'error': 'Invalid token type.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a new short-lived access token
        new_access_payload = {
            'contact_number': decoded['contact_number'],
            'type': 'access',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES)
        }
        new_access_token = jwt.encode(new_access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        return Response({'success': True, 'response': {
            'access_token': new_access_token
        }}, status=status.HTTP_200_OK)

    except jwt.ExpiredSignatureError:
        return Response({'success': False, 'error': 'Refresh token expired. Please log in again.'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({'success': False, 'error': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)


from .decorators import admin_login_required

# -----------------------------------------------------------
# STEP 6: Decode JWT Token (GET request)
# -----------------------------------------------------------
@api_view(['GET'])
@admin_login_required
def decode_token(request):
    # The admin_login_required decorator handles token decoding and user authentication.
    # If the token is valid, the authenticated user is available in request.admin_user.
    
    decoded_data = {
        'contact_number': request.admin_user.contact_number,
        'name': request.admin_user.name,
        'email': request.admin_user.email,
    }
    
    return Response({'success': True, 'decoded_data': decoded_data}, status=status.HTTP_200_OK)

# Force reload

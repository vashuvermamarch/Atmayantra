from rest_framework.decorators import api_view, parser_classes
from .decorators import admin_login_required
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.conf import settings
from .models import AdminUser
from django.contrib.auth.hashers import make_password, check_password
from .serializers import AdminVerifyOtpSerializer
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
        password=make_password(data['password'])  # FIX: Hash password on creation
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

    # FIX: Use check_password to compare plain text against a hash
    if not check_password(password, admin_user.password):
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


# -----------------------------------------------------------
# STEP 7: Logout
# -----------------------------------------------------------
@api_view(['POST'])
@admin_login_required
def logout(request):
    try:
        user = request.admin_user
        user.refresh_token = None
        user.save()
        return Response({'success': True, 'response': {'message': 'Logout successful.'}}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------
# STEP 8: Resend Signup OTP
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def resend_signup_otp(request):
    contact_number = request.data.get('contact_number')
    if not contact_number:
        return Response({'success': False, 'error': 'Contact number is required.'}, status=status.HTTP_400_BAD_REQUEST)

    cached_data = cache.get(f"signup_otp_{contact_number}")
    if not cached_data:
        return Response({'success': False, 'error': 'No active signup process found for this contact number.'}, status=status.HTTP_400_BAD_REQUEST)

    otp = str(random.randint(100000, 999999))
    cached_data['otp'] = otp
    cache.set(f"signup_otp_{contact_number}", cached_data, timeout=settings.OTP_EXPIRY_MINUTES * 60)

    return Response({'success': True, 'response': {
        'message': 'New OTP generated successfully (valid for 15 minutes)',
        'otp': otp,
        'contact_number': contact_number
    }}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 9: Resend Login OTP
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def resend_login_otp(request):
    contact_number = request.data.get('contact_number')
    if not contact_number:
        return Response({'success': False, 'error': 'Contact number is required.'}, status=status.HTTP_400_BAD_REQUEST)

    cached_otp = cache.get(f"login_otp_{contact_number}")
    if not cached_otp:
        return Response({'success': False, 'error': 'No active login process found for this contact number.'}, status=status.HTTP_400_BAD_REQUEST)

    otp = str(random.randint(100000, 999999))
    cache.set(f"login_otp_{contact_number}", otp, timeout=settings.OTP_EXPIRY_MINUTES * 60)

    return Response({'success': True, 'response': {
        'message': 'New OTP generated successfully (valid for 15 minutes)',
        'otp': otp,
        'contact_number': contact_number
    }}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# Resend Reset Password OTP
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def resend_reset_password_otp(request):
    contact_number = request.data.get('contact_number')
    if not contact_number:
        return Response({'success': False, 'error': 'Contact number is required.'}, status=status.HTTP_400_BAD_REQUEST)

    cached_otp = cache.get(f"reset_password_otp_{contact_number}")
    if not cached_otp:
        return Response({'success': False, 'error': 'No active password reset process found for this contact number.'}, status=status.HTTP_400_BAD_REQUEST)

    otp = str(random.randint(100000, 999999))
    cache.set(f"reset_password_otp_{contact_number}", otp, timeout=settings.OTP_EXPIRY_MINUTES * 60)

    return Response({'success': True, 'response': {
        'message': 'New password reset OTP generated successfully (valid for 15 minutes)',
        'otp': otp,
        'contact_number': contact_number
    }}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 10: Forgot Password Request
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def forgot_password_request(request):
    contact_number = request.data.get('contact_number')
    email = request.data.get('email')

    if not contact_number or not email:
        return Response({'success': False, 'error': 'Contact number and email are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AdminUser.objects.get(contact_number=contact_number, email=email)
    except AdminUser.DoesNotExist:
        return Response({'success': False, 'error': 'User with provided contact number and email not found.'}, status=status.HTTP_404_NOT_FOUND)

    otp = str(random.randint(100000, 999999))
    cache.set(f"reset_password_otp_{contact_number}", otp, timeout=settings.OTP_EXPIRY_MINUTES * 60)

    return Response({'success': True, 'response': {
        'message': 'OTP for password reset generated successfully (valid for 15 minutes)',
        'otp': otp,
        'contact_number': contact_number
    }}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 11: Verify OTP for Password Reset
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def verify_reset_otp(request):
    serializer = AdminVerifyOtpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    contact_number = serializer.validated_data['contact_number']
    otp = serializer.validated_data['otp']

    cached_otp = cache.get(f"reset_password_otp_{contact_number}")
    if not cached_otp:
        return Response({'success': False, 'error': 'OTP expired or not found.'}, status=status.HTTP_400_BAD_REQUEST)

    if cached_otp != otp:
        return Response({'success': False, 'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    # OTP is valid, generate a temporary token for the final reset step
    reset_token_payload = {
        'contact_number': contact_number,
        'type': 'password_reset',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    }
    reset_token = jwt.encode(reset_token_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Clean up the OTP from cache as it's been used
    cache.delete(f"reset_password_otp_{contact_number}")

    return Response({'success': True, 'response': {
        'message': 'OTP verified successfully. Use this token to reset your password.',
        'reset_token': reset_token
    }}, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 12: Reset Password with Token
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def reset_password(request):
    reset_token = request.data.get('reset_token')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    if not all([reset_token, password, confirm_password]):
        return Response({'success': False, 'error': 'Reset token and passwords are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({'success': False, 'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        decoded = jwt.decode(reset_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if decoded.get('type') != 'password_reset':
            return Response({'success': False, 'error': 'Invalid token type for password reset.'}, status=status.HTTP_400_BAD_REQUEST)

        contact_number = decoded['contact_number']
        user = AdminUser.objects.get(contact_number=contact_number)
        user.password = make_password(password)
        user.save()
        return Response({'success': True, 'response': {'message': 'Password reset successful.'}}, status=status.HTTP_200_OK)
    except jwt.ExpiredSignatureError:
        return Response({'success': False, 'error': 'Reset token has expired. Please start over.'}, status=status.HTTP_401_UNAUTHORIZED)
    except (jwt.InvalidTokenError, AdminUser.DoesNotExist):
        return Response({'success': False, 'error': 'Invalid token or user not found.'}, status=status.HTTP_401_UNAUTHORIZED)
    except AdminUser.DoesNotExist:
        return Response({'success': False, 'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

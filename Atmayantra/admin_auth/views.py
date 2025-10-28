from rest_framework.decorators import api_view, parser_classes
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
        return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

    if AdminUser.objects.filter(contact_number=contact_number).exists():
        return Response({'error': 'Contact number already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    if AdminUser.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    otp = str(random.randint(100000, 999999))
    cache.set(f"signup_otp_{contact_number}", {'otp': otp, 'data': {
        'contact_number': contact_number,
        'name': name,
        'email': email,
        'password': password
    }}, timeout=settings.OTP_EXPIRY_MINUTES * 60)

    return Response({
        'message': 'OTP generated successfully (valid for 15 minutes)',
        'otp': otp,
        'contact_number': contact_number,
        'email': email
    }, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 2: Verify Signup OTP
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def verify_signup(request):
    contact_number = request.data.get('contact_number')
    otp = request.data.get('otp')

    if not contact_number or not otp:
        return Response({'error': 'Contact number and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

    cached_data = cache.get(f"signup_otp_{contact_number}")
    if not cached_data:
        return Response({'error': 'OTP expired or not found.'}, status=status.HTTP_400_BAD_REQUEST)

    if cached_data['otp'] != otp:
        return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    data = cached_data['data']
    AdminUser.objects.create(
        contact_number=data['contact_number'],
        name=data['name'],
        email=data['email'],
        password=data['password']
    )
    cache.delete(f"signup_otp_{contact_number}")

    return Response({'message': 'Signup successful!'}, status=status.HTTP_201_CREATED)


# -----------------------------------------------------------
# STEP 3: Login Request (Generate OTP)
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def login_request(request):
    contact_number = request.data.get('contact_number')
    password = request.data.get('password')

    if not contact_number or not password:
        return Response({'error': 'Contact number and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        admin_user = AdminUser.objects.get(contact_number=contact_number)
    except AdminUser.DoesNotExist:
        return Response({'error': 'Invalid contact number or password.'}, status=status.HTTP_400_BAD_REQUEST)

    if admin_user.password != password:
        return Response({'error': 'Invalid contact number or password.'}, status=status.HTTP_400_BAD_REQUEST)

    otp = str(random.randint(100000, 999999))
    cache.set(f"login_otp_{contact_number}", otp, timeout=settings.OTP_EXPIRY_MINUTES * 60)

    return Response({
        'message': 'Login OTP generated successfully (valid for 15 minutes)',
        'contact_number': admin_user.contact_number,
        'email': admin_user.email,
        'otp': otp
    }, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 4: Verify Login OTP → Return JWT
# -----------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def verify_login_otp(request):
    contact_number = request.data.get('contact_number')
    otp = request.data.get('otp')

    if not contact_number or not otp:
        return Response({'error': 'Contact number and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

    cached_otp = cache.get(f"login_otp_{contact_number}")
    if cached_otp is None:
        return Response({'error': 'OTP expired or not found.'}, status=status.HTTP_400_BAD_REQUEST)

    if cached_otp != otp:
        return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    cache.delete(f"login_otp_{contact_number}")

    # Get user and generate JWT token
    try:
        user = AdminUser.objects.get(contact_number=contact_number)
    except AdminUser.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    payload = {
        'contact_number': user.contact_number,
        'name': user.name,
        'email': user.email,
        'exp': datetime.datetime.utcnow() + settings.JWT_EXP_DELTA
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return Response({
        'message': 'Login successful!',
        'token': token
    }, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# STEP 5: Decode JWT Token (GET request)
# -----------------------------------------------------------
@api_view(['GET'])
def decode_token(request):
    # Try getting token from Authorization header or query param
    auth_header = request.headers.get('Authorization')
    token = None

    # Option 1: Bearer token from header
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    # Option 2: token from query parameter
    elif request.query_params.get('token'):
        token = request.query_params.get('token')

    if not token:
        return Response({'error': 'Authorization token missing.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return Response({'decoded_data': decoded}, status=status.HTTP_200_OK)
    except jwt.ExpiredSignatureError:
        return Response({'error': 'Token has expired.'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({'error': 'Invalid token.'}, status=status.HTTP_401_UNAUTHORIZED)

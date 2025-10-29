from functools import wraps
from rest_framework.response import Response
from rest_framework import status
import jwt
from django.conf import settings
from .models import AdminUser

def admin_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = None

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return Response({'error': 'Authorization token missing.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
            if decoded.get('type') != 'access':
                return Response({'error': 'Invalid token type.'}, status=status.HTTP_401_UNAUTHORIZED)

            contact_number = decoded.get('contact_number')
            if not contact_number:
                return Response({'error': 'Token is missing user identification.'}, status=status.HTTP_401_UNAUTHORIZED)

            admin_user = AdminUser.objects.get(contact_number=contact_number)
            request.admin_user = admin_user

        except jwt.ExpiredSignatureError:
            return Response({'error': 'Token has expired.'}, status=status.HTTP_401_UNAUTHORIZED)
        except (jwt.InvalidTokenError, AdminUser.DoesNotExist):
            return Response({'error': 'Invalid token or user not found.'}, status=status.HTTP_401_UNAUTHORIZED)

        return view_func(request, *args, **kwargs)
    return _wrapped_view

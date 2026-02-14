from functools import wraps
from rest_framework.response import Response
from rest_framework import status
import jwt
from django.conf import settings
from .models import AdminUser
import datetime

def admin_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Authorization token missing.'}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(' ')[1]

        try:
            # Decode the token to check for expiration
            decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
            # Check if it's an access token
            if decoded.get('type') != 'access':
                return Response({'success': False, 'error': 'Invalid token type.'}, status=status.HTTP_401_UNAUTHORIZED)

            # Get user from token
            contact_number = decoded.get('contact_number')
            if not contact_number:
                return Response({'success': False, 'error': 'Token is missing user identification.'}, status=status.HTTP_401_UNAUTHORIZED)

            # Attach user to request
            request.admin_user = AdminUser.objects.get(contact_number=contact_number)

        except jwt.ExpiredSignatureError:
            # If the token is expired, try to refresh it
            try:
                # Decode without verification to get the payload
                unverified_payload = jwt.decode(token, algorithms=[settings.JWT_ALGORITHM], options={"verify_signature": False})
                contact_number = unverified_payload.get('contact_number')

                if not contact_number:
                    return Response({'success': False, 'error': 'Invalid token (no contact number).'}, status=status.HTTP_401_UNAUTHORIZED)

                # Get the user and their refresh token
                user = AdminUser.objects.get(contact_number=contact_number)
                refresh_token = user.refresh_token

                if not refresh_token:
                    return Response({'success': False, 'error': 'Please log in again (no refresh token).'}, status=status.HTTP_401_UNAUTHORIZED)

                # Verify the refresh token
                decoded_refresh = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                if decoded_refresh.get('type') != 'refresh':
                    return Response({'success': False, 'error': 'Invalid refresh token type.'}, status=status.HTTP_401_UNAUTHORIZED)

                # Generate a new access token
                new_access_payload = {
                    'contact_number': user.contact_number,
                    'name': user.name,
                    'email': user.email,
                    'type': 'access',
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES)
                }
                new_access_token = jwt.encode(new_access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

                # Re-attach user to the request and proceed
                request.admin_user = user
                
                # Call the view function and add the new token to the response
                response = view_func(request, *args, **kwargs)
                response.data['new_access_token'] = new_access_token
                response.data['message'] = "Your access token was refreshed."
                return response

            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, AdminUser.DoesNotExist):
                return Response({'success': False, 'error': 'Session expired. Please log in again.'}, status=status.HTTP_401_UNAUTHORIZED)

        except (jwt.InvalidTokenError, AdminUser.DoesNotExist):
            return Response({'success': False, 'error': 'Invalid token or user not found.'}, status=status.HTTP_401_UNAUTHORIZED)

        return view_func(request, *args, **kwargs)
    return _wrapped_view

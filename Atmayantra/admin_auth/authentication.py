import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import AdminUser


class AdminJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split(" ")

            if prefix != "Bearer":
                return None

            decoded = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            if decoded.get("type") != "access":
                raise AuthenticationFailed("Invalid admin token")

            admin = AdminUser.objects.get(
                contact_number=decoded["contact_number"]
            )

            request.admin_user = admin

            return (admin, None)

        except Exception:
            return None

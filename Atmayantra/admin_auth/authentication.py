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

            # 1. Unverified decode check for Admin-specific fields
            try:
                unverified = jwt.decode(token, options={"verify_signature": False})
                is_admin_token = "contact_number" in unverified and ("email" in unverified or unverified.get("type") == "access")
            except Exception:
                # If we cannot even decode it, it's not a valid token format for us
                return None

            if not is_admin_token:
                # This doesn't look like an Admin token, let other authenticators try
                return None

            # 2. Verified decode - We are confident this is an Admin token
            try:
                decoded = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )

                if decoded.get("type") != "access":
                     raise AuthenticationFailed("Invalid admin token type")

                admin = AdminUser.objects.get(
                    contact_number=decoded["contact_number"]
                )

                request.admin_user = admin
                return (admin, None)

            except jwt.ExpiredSignatureError:
                raise AuthenticationFailed("Admin access token has expired")
            except jwt.InvalidTokenError:
                raise AuthenticationFailed("Invalid Admin access token signature")
            except AdminUser.DoesNotExist:
                raise AuthenticationFailed("Admin user account not found")

        except Exception as e:
            if isinstance(e, AuthenticationFailed):
                raise e
            return None

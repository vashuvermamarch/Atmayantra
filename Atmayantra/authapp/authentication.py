# Code Add me here
def allow_any_user(user):
    """
    Custom authentication rule for SimpleJWT.
    Allows inactive users (like pending Trainers) to authenticate with their token
    so they can submit their personal details and documents for admin approval.
    """
    return True


# Code add with me
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from django.utils.translation import gettext_lazy as _

class SoftJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that allows INACTIVE users to authenticate.
    This allows non-approved users (Physio, Doctor, etc.) to use IsAuthenticated
    endpoints so they can upload their documents.
    """
    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        # WE REMOVED THE is_active CHECK ENTIRELY FOR ONBOARDING
        return user
#======================

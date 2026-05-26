from rest_framework_simplejwt.tokens import RefreshToken


class CustomRefreshToken(RefreshToken):

    @classmethod
    def for_user(cls, user):

        token = super().for_user(user)

        token["username"] = user.username
        token["phone_number"] = user.phone_number
        token["user_type"] = user.user_type
        token["is_verified"] = user.is_verified
        token["is_active"] = user.is_active

        return token

from functools import wraps
from rest_framework.response import Response
from rest_framework import status

def check_user_role(role):
    """
    A decorator to check if a user has a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # Assuming the user model has a 'role' attribute
            if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == role:
                return view_func(self, request, *args, **kwargs)
            else:
                return Response(
                    {"error": "You do not have permission to perform this action."},
                    status=status.HTTP_403_FORBIDDEN
                )
        return _wrapped_view
    return decorator

def login_required(view_func):
    """
    A decorator to check if a user is authenticated.
    """
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return view_func(self, request, *args, **kwargs)
    return _wrapped_view

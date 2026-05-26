from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAuthenticatedOrPostOnly(BasePermission):
    """
    Custom permission to allow unauthenticated POST requests,
    but require authentication for all other methods.
    """
    def has_permission(self, request, view):
        # Allow all POST requests without authentication.
        if request.method == 'POST':
            return True

        # For all other methods, enforce standard authentication.
        return IsAuthenticated().has_permission(request, view)

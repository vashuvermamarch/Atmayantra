from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Contact
from .serializers import ContactSerializer
from Atmayantra.utils import api_response
from authapp.decorators import login_required
import os
import logging

logger = logging.getLogger(__name__)

class ContactViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ContactSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        logger.info(f"Contact created with ID: {serializer.instance.id}")
        
        return api_response(True, "Contact created successfully.", serializer.data, status_code=status.HTTP_201_CREATED)

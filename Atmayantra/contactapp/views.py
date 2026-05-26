import logging

from Atmayantra.utils import api_response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Contact
from .serializers import ContactSerializer

logger = logging.getLogger(__name__)

class ContactViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ContactSerializer
    queryset = Contact.objects.all()

    # -----------------------------
    # CREATE (POST)
    # -----------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return api_response(
                False,
                "Invalid data provided.",
                serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
        logger.info(f"Contact created with ID: {serializer.instance.id}")

        return api_response(
            True,
            "Contact created successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK      # <<< FIXED (was 201)
        )

    # -----------------------------
    # LIST (GET /contacts/)
    # -----------------------------
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return api_response(
            True,
            "Contacts retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK
        )

    # -----------------------------
    # RETRIEVE (GET /contacts/{id}/)
    # -----------------------------
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return api_response(
            True,
            "Contact retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK
        )

    # -----------------------------
    # UPDATE (PUT)
    # -----------------------------
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data)
        if not serializer.is_valid():
            return api_response(
                False,
                "Invalid data provided.",
                serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        self.perform_update(serializer)

        return api_response(
            True,
            "Contact updated successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK
        )

    # -----------------------------
    # PARTIAL UPDATE (PATCH)
    # -----------------------------
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_response(
                False,
                "Invalid data provided.",
                serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        self.perform_update(serializer)

        return api_response(
            True,
            "Contact updated successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK
        )

    # -----------------------------
    # DELETE (DELETE)
    # -----------------------------
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        return api_response(
            True,
            "Contact deleted successfully.",
            status_code=status.HTTP_200_OK
        )

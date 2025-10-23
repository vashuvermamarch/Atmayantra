from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Contact
from .serializers import ContactSerializer
# 1. Import the api_response helper
from Atmayantra.utils import api_response
import os

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    lookup_field = 'phone_no'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        response_data = {
            "status": "success",
            "message": "Contact created successfully.",
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    # 4. Example: A custom action that returns a sample error (HTTP 404)
    @action(detail=False, methods=['get'])
    def sample_error(self, request):
        return api_response(success=False, message="Resource not found.", status_code=status.HTTP_404_NOT_FOUND)

    # 5. Example: A custom action that returns a file download
    @action(detail=False, methods=['get'])
    def download_image(self, request):
        # This is a placeholder. Ensure 'media/sample.jpg' exists in your project's root.
        # You can create a 'media' folder and place any JPG file there.
        file_path = os.path.join('media', 'sample.jpg')
        try:
            file_handle = open(file_path, 'rb')
            # The api_response helper detects the file and returns a FileResponse.
            return api_response(file=file_handle)
        except FileNotFoundError:
            return api_response(success=False, message="File not found. Please create 'media/sample.jpg'.", status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return api_response(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

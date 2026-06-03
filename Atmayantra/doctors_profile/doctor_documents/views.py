from rest_framework.views import APIView
from rest_framework import status
from django.core.cache import cache
from django.http import HttpResponse
import base64
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import uuid
from doctors_profile.doctor_personal_details.models import DoctorPersonalDetails

from .serializers import DoctorDocumentSerializer
from .models import DoctorDocument
from Atmayantra.utils import api_response
from common.permissions import IsAuthenticatedOrPostOnly

CACHE_TIMEOUT = 86400  # 24 hours

class DoctorDocumentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrPostOnly]

    def post(self, request, *args, **kwargs):
        contact_number = request.data.get('doctor')
        if not contact_number:
            return api_response(False, "'doctor' (contact number) is a required field.", status_code=status.HTTP_400_BAD_REQUEST)

        serializer = DoctorDocumentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Always save to cache during onboarding
            # First, check if step 1 was completed
            personal_details_cache_key = f"doctor_personal_details_{contact_number}"
            if not cache.get(personal_details_cache_key):
                return api_response(False, "Personal details for this doctor do not exist in cache. Please complete step 1 first.", status_code=status.HTTP_400_BAD_REQUEST)

            # Prepare document data for caching
            doc_type = data.get('doc_type')
            side = data.get('side')
            file_dict = data.get('file')

            documents_cache_key = f"doctor_documents_{contact_number}"
            documents = cache.get(documents_cache_key, [])

            document_id = str(uuid.uuid4())
            document_data = {
                'id': document_id,
                'doc_type': doc_type,
                'side': side,
                'file': file_dict
            }
            documents.append(document_data)
            
            # Save the updated list of documents back to the cache
            cache.set(documents_cache_key, documents, timeout=CACHE_TIMEOUT)

            return api_response(True, "Step 3 of 4: Document saved temporarily.", {'document_id': document_id}, status_code=status.HTTP_200_OK)
        
        return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def get(self, request, contact_number, *args, **kwargs):
        documents_cache_key = f"doctor_documents_{contact_number}"
        documents = cache.get(documents_cache_key)

        if documents is None:
            # If not in cache, try to get from the database
            try:
                doctor_documents = DoctorDocument.objects.filter(doctor__contact_number=contact_number)
                if not doctor_documents.exists():
                    return api_response(False, "No documents found for this doctor.", status_code=status.HTTP_404_NOT_FOUND)

                # Serialize the documents
                serializer = DoctorDocumentSerializer(doctor_documents, many=True)
                documents = serializer.data
                
                # Store in cache for future requests
                cache.set(documents_cache_key, documents, timeout=CACHE_TIMEOUT)

            except Exception as e:
                return api_response(False, f"An error occurred: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return api_response(True, "Documents retrieved successfully.", documents)

    def put(self, request, contact_number, document_id, *args, **kwargs):
        """
        Updates a document in the database (full update).
        """
        try:
            document = DoctorDocument.objects.get(id=document_id, doctor__contact_number=contact_number)
        except DoctorDocument.DoesNotExist:
            return api_response(False, "Document not found.", status_code=status.HTTP_404_NOT_FOUND)

        # We pass the instance to the serializer for update
        serializer = DoctorDocumentSerializer(document, data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            
            # Handle file update if a new file is provided
            if 'file' in validated_data:
                file_dict = validated_data.pop('file')
                document.file_data = file_dict.get('content')
                document.filename = file_dict.get('filename')
                document.content_type = file_dict.get('content_type')

            # Update other fields
            document.doc_type = validated_data.get('doc_type', document.doc_type)
            document.side = validated_data.get('side', document.side)
            document.save()

            # Return the updated data
            response_serializer = DoctorDocumentSerializer(document)
            return api_response(True, "Document updated successfully.", response_serializer.data, status_code=status.HTTP_200_OK)
        
        return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, contact_number, document_id, *args, **kwargs):
        """
        Partially updates a document in the database.
        """
        try:
            document = DoctorDocument.objects.get(id=document_id, doctor__contact_number=contact_number)
        except DoctorDocument.DoesNotExist:
            return api_response(False, "Document not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Use partial=True for PATCH requests
        serializer = DoctorDocumentSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            validated_data = serializer.validated_data

            # Handle file update if a new file is provided
            if 'file' in validated_data:
                file_dict = validated_data.pop('file')
                document.file_data = file_dict.get('content')
                document.filename = file_dict.get('filename')
                document.content_type = file_dict.get('content_type')

            # Update other fields if they are in the request
            if 'doc_type' in validated_data:
                document.doc_type = validated_data.get('doc_type')
            if 'side' in validated_data:
                document.side = validated_data.get('side')
            document.save()

            response_serializer = DoctorDocumentSerializer(document)
            return api_response(True, "Document updated successfully.", response_serializer.data, status_code=status.HTTP_200_OK)
        
        return api_response(False, "Invalid data provided.", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, contact_number, document_id, *args, **kwargs):
        """
        Deletes a document from the database and cache.
        """
        try:
            # First, delete from the database
            document = DoctorDocument.objects.get(id=document_id, doctor__contact_number=contact_number)
            document.delete()
            
            # Then, remove from cache if it exists
            documents_cache_key = f"doctor_documents_{contact_number}"
            documents = cache.get(documents_cache_key)
            if documents:
                updated_documents = [doc for doc in documents if doc.get('id') != document_id]
                if len(updated_documents) < len(documents):
                    cache.set(documents_cache_key, updated_documents, timeout=CACHE_TIMEOUT)

            return api_response(True, "Document deleted successfully.", status_code=status.HTTP_200_OK)

        except DoctorDocument.DoesNotExist:
            # If not in DB, try to delete from cache anyway
            documents_cache_key = f"doctor_documents_{contact_number}"
            documents = cache.get(documents_cache_key)
            if documents:
                document_found = False
                updated_documents = []
                for doc in documents:
                    if doc.get('id') == document_id:
                        document_found = True
                    else:
                        updated_documents.append(doc)
                
                if document_found:
                    cache.set(documents_cache_key, updated_documents, timeout=CACHE_TIMEOUT)
                    return api_response(True, "Document deleted successfully from cache.", status_code=status.HTTP_200_OK)

            return api_response(False, "Document not found.", status_code=status.HTTP_404_NOT_FOUND)

class DoctorDocumentDownloadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, contact_number, document_id, *args, **kwargs):
        try:
            document = DoctorDocument.objects.get(id=document_id, doctor__contact_number=contact_number)
            
            file_data_b64 = document.file_data
            if not file_data_b64:
                return api_response(False, "File data not found for this document.", status_code=status.HTTP_404_NOT_FOUND)

            try:
                # Handle potential data URI scheme
                if ',' in file_data_b64:
                    header, encoded = file_data_b64.split(',', 1)
                else:
                    encoded = file_data_b64
                
                file_data = base64.b64decode(encoded)
            except (ValueError, TypeError) as e:
                return api_response(False, f"Error decoding file data: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            response = HttpResponse(file_data, content_type=document.content_type)
            response['Content-Disposition'] = f'attachment; filename="{document.filename}"'
            return response

        except DoctorDocument.DoesNotExist:
            return api_response(False, "Document not found.", status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return api_response(False, f"An error occurred: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

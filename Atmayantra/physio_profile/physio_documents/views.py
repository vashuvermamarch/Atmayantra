from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from .models import PhysioDocumentation
from .serializers import PhysioDocumentationSerializer
from physio_profile.utils import file_to_b64

CACHE_TIMEOUT = 86400

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_documentation(request):
    if request.user.user_type != 'Physiotherapist':
        return Response({"error": "Only Physiotherapists can access this."}, status=status.HTTP_403_FORBIDDEN)
        
    cache_key = f"physio_step3_{request.user.id}"

    if request.method == 'GET':
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({"success": True, "message": "Fetched from temporary memory (documents present).", "data": {"status": "Cached documents exist."}}, status=status.HTTP_200_OK)
        
        try:
            docs = PhysioDocumentation.objects.get(user=request.user)
            serializer = PhysioDocumentationSerializer(docs)
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except PhysioDocumentation.DoesNotExist:
            return Response({"success": True, "data": {}}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        old_cache = cache.get(cache_key) or {}
        data_to_cache = {}
        
        # Files keys expected
        keys = ['aadhar_card_front', 'aadhar_card_back', 'pancard', 'resume_cv', 'certificate']
        for k in keys:
            if k in request.FILES:
                data_to_cache[f"{k}_b64"] = file_to_b64(request.FILES[k])
            elif f"{k}_b64" in old_cache:
                data_to_cache[f"{k}_b64"] = old_cache[f"{k}_b64"]
                
        cache.set(cache_key, data_to_cache, timeout=CACHE_TIMEOUT)
        
        return Response({
            "success": True, 
            "message": "Step 3 complete. Documents temporarily saved."
        }, status=status.HTTP_200_OK)

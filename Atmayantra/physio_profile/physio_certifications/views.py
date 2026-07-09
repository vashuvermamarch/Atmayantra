from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PhysioCertification
from .serializers import PhysioCertificationSerializer

CACHE_TIMEOUT = 86400

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_certification(request):
    if request.user.user_type != 'Physiotherapist':
        return Response({"error": "Only Physiotherapists can access this."}, status=status.HTTP_403_FORBIDDEN)

    cache_key = f"physio_step2_{request.user.id}"

    if request.method == 'GET':
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({"success": True, "message": "Fetched from temporary memory", "data": cached_data}, status=status.HTTP_200_OK)

        try:
            cert = PhysioCertification.objects.get(user=request.user)
            serializer = PhysioCertificationSerializer(cert)
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except PhysioCertification.DoesNotExist:
            return Response({"success": True, "data": {}}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data_to_cache = request.POST.dict() if request.POST else request.data
        cache.set(cache_key, data_to_cache, timeout=CACHE_TIMEOUT)

        return Response({
            "success": True,
            "message": "Step 2 complete. Certifications temporarily saved."
        }, status=status.HTTP_200_OK)

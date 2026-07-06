from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from .models import PhysioPersonalDetails
from .serializers import PhysioPersonalDetailsSerializer
from physio_profile.utils import file_to_b64

CACHE_TIMEOUT = 86400  # 24 hours

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_personal_details(request):
    if request.user.user_type != 'Physiotherapist':
        return Response({"error": "Only Physiotherapists can access this."}, status=status.HTTP_403_FORBIDDEN)
        
    cache_key = f"physio_step1_{request.user.id}"

    if request.method == 'GET':
        # Check cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            # Drop the large base64 string from response to avoid lag, frontend just needs text fields
            display_data = {k: v for k, v in cached_data.items() if k != 'profile_photo_b64'}
            display_data['has_cached_photo'] = 'profile_photo_b64' in cached_data
            return Response({"success": True, "message": "Fetched from temporary memory", "data": display_data}, status=status.HTTP_200_OK)
        
        # Else check DB
        try:
            details = PhysioPersonalDetails.objects.get(user=request.user)
            serializer = PhysioPersonalDetailsSerializer(details, context={'request': request})
            return Response({"success": True, "message": "Fetched from Database", "data": serializer.data}, status=status.HTTP_200_OK)
        except PhysioPersonalDetails.DoesNotExist:
            return Response({"success": True, "data": {}}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # We save everything in dict to cache
        data_to_cache = request.POST.dict() 
        
        # If there's an image
        if 'profile_photo' in request.FILES:
            photo = request.FILES['profile_photo']
            data_to_cache['profile_photo_b64'] = file_to_b64(photo)
        else:
            # Keep previous cached photo if they just updated text
            old_cache = cache.get(cache_key)
            if old_cache and 'profile_photo_b64' in old_cache:
                data_to_cache['profile_photo_b64'] = old_cache['profile_photo_b64']
                
        cache.set(cache_key, data_to_cache, timeout=CACHE_TIMEOUT)
        
        return Response({
            "success": True, 
            "message": "Step 1 complete. Data temporarily saved."
        }, status=status.HTTP_200_OK)


from django.http import HttpResponse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_profile_photo(request):
    if request.user.user_type != 'Physiotherapist':
        return Response({"error": "Only Physiotherapists can access this."}, status=status.HTTP_403_FORBIDDEN)
    try:
        details = PhysioPersonalDetails.objects.get(user=request.user)
        if details.profile_photo:
            return HttpResponse(
                details.profile_photo,
                content_type=details.profile_photo_mimetype or 'image/jpeg'
            )
    except PhysioPersonalDetails.DoesNotExist:
        pass
    return Response({"error": "Profile photo not found."}, status=status.HTTP_404_NOT_FOUND)

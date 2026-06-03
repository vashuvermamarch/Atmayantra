from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status

from admin_auth.decorators import admin_login_required
from authapp.models import User

# =============================================================
# PHYSIO APPROVAL ENDPOINTS (Admin ke liye)
# =============================================================

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
@admin_login_required
def get_pending_physios(request):
    status_filter = request.GET.get('status')
    qs = User.objects.filter(user_type='Physiotherapist')

    if status_filter == 'pending':
        qs = qs.filter(is_active=False)
    elif status_filter == 'approved':
        qs = qs.filter(is_active=True)

    physios = []
    for physio in qs:
        physios.append({
            "id": physio.id,
            "username": physio.username,
            "phone": physio.phone_number,
            "email": physio.email,
            "user_type": physio.user_type,
            "is_active": physio.is_active,
            "is_verified": physio.is_verified,
        })

    return Response({
        "success": True,
        "response": {
            "total": len(physios),
            "physios": physios
        }
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@admin_login_required
def approve_physio(request, physio_id):
    try:
        physio_user = User.objects.get(id=physio_id, user_type='Physiotherapist')
    except User.DoesNotExist:
        return Response({"success": False, "message": f"No Physiotherapist found with id: {physio_id}"}, status=status.HTTP_404_NOT_FOUND)

    physio_user.is_active = True
    physio_user.save()

    return Response({
        "success": True,
        "message": "Physiotherapist approved successfully!",
        "physio": {"username": physio_user.username, "phone": physio_user.phone_number, "is_active": physio_user.is_active}
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@admin_login_required
def reject_physio(request, physio_id):
    try:
        physio_user = User.objects.get(id=physio_id, user_type='Physiotherapist')
    except User.DoesNotExist:
        return Response({"success": False, "message": f"No Physiotherapist found with id: {physio_id}"}, status=status.HTTP_404_NOT_FOUND)

    physio_user.is_active = False
    physio_user.save()

    return Response({
        "success": True,
        "message": "Physiotherapist rejected. Account remains inactive.",
        "physio": {"username": physio_user.username, "phone": physio_user.phone_number, "is_active": physio_user.is_active}
    })

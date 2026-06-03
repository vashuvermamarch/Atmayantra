from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status

from admin_auth.decorators import admin_login_required
from authapp.models import User


# =============================================================
# DOCTOR APPROVAL ENDPOINTS (Admin ke liye)
# =============================================================

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
@admin_login_required
def get_pending_doctors(request):
    """
    Admin: Sabhi pending (inactive + verified) doctors ki list.
    Query param: ?status=pending / ?status=approved / kuch nahi = sab
    User type filter: Yoga Doctor
    """
    status_filter = request.GET.get('status')

    # Sabhi Yoga Doctors fetch karo
    qs = User.objects.filter(user_type='Yoga Doctor')

    if status_filter == 'pending':
        qs = qs.filter(is_active=False)    # pending = inactive (verified ya nahi)
    elif status_filter == 'approved':
        qs = qs.filter(is_active=True)

    doctors = []
    for doc in qs:
        doctors.append({
            "id": doc.id,
            "username": doc.username,
            "phone": doc.phone_number,
            "email": doc.email,
            "user_type": doc.user_type,
            "is_active": doc.is_active,
            "is_verified": doc.is_verified,
        })

    return Response({
        "success": True,
        "response": {
            "total": len(doctors),
            "doctors": doctors
        }
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@admin_login_required
def approve_doctor(request, doctor_id):
    """
    Admin: Doctor ko approve karo.
    URL: /api/doctors/profile/approve/<doctor_id>/
    Doctor ka is_active = True ho jayega.
    """
    try:
        doctor_user = User.objects.get(
            id=doctor_id,
            user_type='Yoga Doctor'
        )
    except User.DoesNotExist:
        return Response({
            "success": False,
            "message": f"No Yoga Doctor found with id: {doctor_id}"
        }, status=status.HTTP_404_NOT_FOUND)

    doctor_user.is_active = True
    doctor_user.save()

    return Response({
        "success": True,
        "message": "Doctor approved successfully!",
        "doctor": {
            "username": doctor_user.username,
            "phone": doctor_user.phone_number,
            "is_active": doctor_user.is_active,
        }
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@admin_login_required
def reject_doctor(request, doctor_id):
    """
    Admin: Doctor ko reject karo.
    URL: /api/doctors/profile/reject/<doctor_id>/
    Doctor ka account deactivate rehega.
    """
    try:
        doctor_user = User.objects.get(
            id=doctor_id,
            user_type='Yoga Doctor'
        )
    except User.DoesNotExist:
        return Response({
            "success": False,
            "message": f"No Yoga Doctor found with id: {doctor_id}"
        }, status=status.HTTP_404_NOT_FOUND)

    doctor_user.is_active = False
    doctor_user.save()

    return Response({
        "success": True,
        "message": "Doctor rejected. Account remains inactive.",
        "doctor": {
            "username": doctor_user.username,
            "phone": doctor_user.phone_number,
            "is_active": doctor_user.is_active,
        }
    })

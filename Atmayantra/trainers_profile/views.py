from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings

from admin_auth.decorators import admin_login_required
from .models import TrainersPersonalDetails
from .serializers import TrainerListSerializer
from .email_service import send_trainer_status_email
# Code change with me
from authapp.models import User


# -----------------------------------------------------------
# ENDPOINT 1:  Trainers List (Admin ke liye)
# -----------------------------------------------------------
@api_view(['GET'])
@admin_login_required
def get_all_trainers(request):
    status_filter = request.GET.get('status')

    if status_filter:
        trainers = TrainersPersonalDetails.objects.filter(
            status=status_filter
        ).order_by('-created_at')
    else:
        trainers = TrainersPersonalDetails.objects.all().order_by('-created_at')

    serializer = TrainerListSerializer(trainers, many=True)

    return Response({
        'success': True,
        'response': {
            'total': trainers.count(),
            'trainers': serializer.data
        }
    }, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# ENDPOINT 2: Trainer Approve
# -----------------------------------------------------------
@api_view(['POST'])
@admin_login_required
def approve_trainer(request, trainer_id):
    try:
        trainer = TrainersPersonalDetails.objects.get(id=trainer_id)
    except TrainersPersonalDetails.DoesNotExist:
        return Response({'success': False, 'error': 'Trainer not found'},
                        status=status.HTTP_404_NOT_FOUND)

    if trainer.status == 'approved':
        return Response({'success': False, 'error': 'Already approved'},
                        status=status.HTTP_400_BAD_REQUEST)

    trainer.status = 'approved'
    trainer.approved_by = request.admin_user
    trainer.save()

    # Code change with me
    # ✅ authapp User ko bhi activate karo taaki trainer login kar sake
    try:
        auth_user = User.objects.get(phone_number=trainer.phone)
        auth_user.is_active = True
        auth_user.save()
    except User.DoesNotExist:
        pass  # User nahi mila toh silently skip

    try:
        send_trainer_status_email(trainer, 'approved')
    except Exception as e:
        print("Email error:", e)

    return Response({
        'success': True,
        'message': 'Trainer approved successfully',
        'trainer_id': trainer.id
    }, status=status.HTTP_200_OK)


# -----------------------------------------------------------
# ENDPOINT 3: Trainer Reject
# -----------------------------------------------------------
@api_view(['POST'])
@admin_login_required
def reject_trainer(request, trainer_id):
    try:
        trainer = TrainersPersonalDetails.objects.get(id=trainer_id)
    except TrainersPersonalDetails.DoesNotExist:
        return Response({'success': False, 'error': 'Trainer not found'},
                        status=status.HTTP_404_NOT_FOUND)

    if trainer.status == 'rejected':
        return Response({'success': False, 'error': 'Already rejected'},
                        status=status.HTTP_400_BAD_REQUEST)

    trainer.status = 'rejected'
    trainer.approved_by = request.admin_user
    trainer.save()

    try:
        send_trainer_status_email(trainer, 'rejected')
    except Exception as e:
        print("Email error:", e)

    return Response({
        'success': True,
        'message': 'Trainer rejected successfully',
        'trainer_id': trainer.id
    }, status=status.HTTP_200_OK)
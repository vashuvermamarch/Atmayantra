from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db import transaction
import base64

from .models import PhysioBankDetails
from .serializers import PhysioBankDetailsSerializer

from physio_profile.physio_personal_details.models import PhysioPersonalDetails
from physio_profile.physio_personal_details.serializers import PhysioPersonalDetailsSerializer

from physio_profile.physio_certifications.models import PhysioCertification
from physio_profile.physio_certifications.serializers import PhysioCertificationSerializer

from physio_profile.physio_documents.models import PhysioDocumentation
from physio_profile.physio_documents.serializers import PhysioDocumentationSerializer

from physio_profile.utils import file_to_b64, b64_to_file

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_bank_details(request):
    if request.user.user_type != 'Physiotherapist':
        return Response({"error": "Only Physiotherapists can access this."}, status=status.HTTP_403_FORBIDDEN)
        
    user_id = request.user.id

    if request.method == 'GET':
        try:
            bank = PhysioBankDetails.objects.get(user=request.user)
            serializer = PhysioBankDetailsSerializer(bank, context={'request': request})
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except PhysioBankDetails.DoesNotExist:
            return Response({"success": True, "data": {}}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Final Submit -> Pull all caches!
        step1 = cache.get(f"physio_step1_{user_id}")
        step2 = cache.get(f"physio_step2_{user_id}")
        step3 = cache.get(f"physio_step3_{user_id}")
        
        if not (step1 and step2 and step3):
            return Response({
                "success": False, 
                "message": "Session expired or missing previous steps. Please re-check from Step 1."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        step4_data = request.POST.dict() if request.POST else request.data
        if 'upload_bank_qr_code' in request.FILES:
            step4_file = request.FILES['upload_bank_qr_code']
        else:
            step4_file = None

        # Prepare to save to DB atomically
        try:
            with transaction.atomic():
                # 1. Personal Details
                pd_obj, _ = PhysioPersonalDetails.objects.get_or_create(user=request.user)
                s1 = PhysioPersonalDetailsSerializer(pd_obj, data=step1, partial=True)
                s1.is_valid(raise_exception=True)
                pd_instance = s1.save()
                if 'profile_photo_b64' in step1:
                    photo_b64 = step1['profile_photo_b64']
                    if photo_b64:
                        pd_instance.profile_photo = base64.b64decode(photo_b64['data'])
                        pd_instance.profile_photo_mimetype = photo_b64['content_type']
                        pd_instance.save()

                # 2. Certification
                cert_obj, _ = PhysioCertification.objects.get_or_create(user=request.user)
                s2 = PhysioCertificationSerializer(cert_obj, data=step2, partial=True)
                s2.is_valid(raise_exception=True)
                s2.save()

                # 3. Documentation
                doc_obj, _ = PhysioDocumentation.objects.get_or_create(user=request.user)
                s3 = PhysioDocumentationSerializer(doc_obj, data={}, partial=True)
                s3.is_valid(raise_exception=True)
                doc_instance = s3.save()
                
                # Assign files
                for f_key in ['aadhar_card_front', 'aadhar_card_back', 'pancard', 'resume_cv', 'certificate']:
                    cache_key = f"{f_key}_b64"
                    if cache_key in step3:
                        b64_dict = step3[cache_key]
                        if b64_dict:
                            setattr(doc_instance, f_key, base64.b64decode(b64_dict['data']))
                            setattr(doc_instance, f"{f_key}_mimetype", b64_dict['content_type'])
                doc_instance.save()

                # 4. Bank Details (Current Step)
                bank_obj, _ = PhysioBankDetails.objects.get_or_create(user=request.user)
                s4 = PhysioBankDetailsSerializer(bank_obj, data=step4_data, partial=True)
                s4.is_valid(raise_exception=True)
                bank_instance = s4.save()
                if step4_file:
                    bank_instance.upload_bank_qr_code = step4_file.read()
                    bank_instance.upload_bank_qr_code_mimetype = step4_file.content_type
                    bank_instance.save()
                    
            # Clear Cache!
            cache.delete(f"physio_step1_{user_id}")
            cache.delete(f"physio_step2_{user_id}")
            cache.delete(f"physio_step3_{user_id}")

            return Response({
                "success": True, 
                "message": "All steps submitted successfully! Data permanently saved."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False, 
                "message": f"Validation/Database Error: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


from django.http import HttpResponse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_bank_qr_code(request):
    try:
        bank = PhysioBankDetails.objects.get(user=request.user)
        if bank.upload_bank_qr_code:
            return HttpResponse(
                bank.upload_bank_qr_code,
                content_type=bank.upload_bank_qr_code_mimetype or 'image/jpeg'
            )
    except PhysioBankDetails.DoesNotExist:
        pass
    return Response({"error": "QR code not found."}, status=status.HTTP_404_NOT_FOUND)

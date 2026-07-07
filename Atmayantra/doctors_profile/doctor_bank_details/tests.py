
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from doctors_profile.doctor_bank_details.models import DoctorBankDetails
from doctors_profile.doctor_certification.models import DoctorCertification
from doctors_profile.doctor_documents.models import DoctorDocument
from doctors_profile.doctor_personal_details.models import DoctorPersonalDetails, DoctorProfilePhoto


class DoctorOnboardingStep4Tests(APITestCase):
    def setUp(self):
        cache.clear()
        self.contact_number = "1234567890"
        self.temp_id = "test_temp_id_step4"

        # 1. Setup session temp_id -> contact_number mapping
        cache.set(f"doctor_onboarding_session_{self.temp_id}", self.contact_number, timeout=3600)

        # 2. Setup cached personal details (Step 1)
        self.personal_data = {
            "contact_number": self.contact_number,
            "full_name": "Dr. John Watson",
            "email": "watson@example.com",
            "gender": "Male",
            "date_of_birth": "1985-05-15",
            "state": "Maharashtra",
            "city": "Mumbai",
            "pincode": "400001",
            "spoken_language": "English, Marathi"
        }
        cache.set(f"doctor_personal_details_{self.contact_number}", self.personal_data, timeout=3600)

        # 3. Setup cached certification details (Step 2)
        self.certification_data = {
            "highest_degree": "MBBS",
            "specialization": "General Medicine",
            "year_of_graduation": 2010,
            "work_experience": "10 years",
            "yoga_certified": True,
            "registration_number": "REG12345",
            "certification_type": "Yoga Therapy",
            "issuing_authority": "QCI",
            "graduation_certificate": "dummy_cert_b64",
            "experience_letter": "dummy_exp_b64",
            "resume_cv": "dummy_resume_b64",
            "license_pdf": "dummy_license_b64",
        }
        cache.set(f"doctor_certification_{self.contact_number}", self.certification_data, timeout=3600)

        # 4. Setup cached documents (Step 3)
        self.documents_data = [
            {
                "id": "doc-uuid-1",
                "doc_type": "Aadhaar Card",
                "side": "front",
                "file": {
                    "content": "dummy_aadhaar_b64",
                    "filename": "aadhaar_front.jpg",
                    "content_type": "image/jpeg"
                }
            }
        ]
        cache.set(f"doctor_documents_{self.contact_number}", self.documents_data, timeout=3600)

        # A mock QR Code file for step 4 POST
        self.mock_qr = SimpleUploadedFile(
            name="qr_code.png",
            content=b"dummy_qr_code_data",
            content_type="image/png"
        )

    def tearDown(self):
        cache.clear()

    def test_finalize_registration_success_with_photo(self):
        # Cache profile photo
        cache.set(f"doctor_profile_photo_{self.contact_number}", "dummy_profile_photo_b64", timeout=3600)

        # Call Step 4 POST
        payload = {
            "temp_id": self.temp_id,
            "account_holder_name": "John Watson",
            "account_number": "123456789012",
            "confirm_account_number": "123456789012",
            "ifsc_code": "SBIN0001234",
            "upi_id": "watson@okaxis",
            "account_type": "Savings",
            "bank_qr_code": self.mock_qr
        }

        response = self.client.post("/api/doctors/bank-details/", payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["status"], "success")

        # Verify DB models created
        self.assertTrue(DoctorPersonalDetails.objects.filter(pk=self.contact_number).exists())
        self.assertTrue(DoctorProfilePhoto.objects.filter(doctor_id=self.contact_number).exists())
        self.assertTrue(DoctorCertification.objects.filter(doctor_id=self.contact_number).exists())
        self.assertTrue(DoctorDocument.objects.filter(doctor_id=self.contact_number).exists())
        self.assertTrue(DoctorBankDetails.objects.filter(doctor_id=self.contact_number).exists())

    def test_finalize_registration_succeeds_missing_photo(self):
        # Do not cache profile photo -> Should succeed without raising errors
        payload = {
            "temp_id": self.temp_id,
            "account_holder_name": "John Watson",
            "account_number": "123456789012",
            "confirm_account_number": "123456789012",
            "ifsc_code": "SBIN0001234",
            "upi_id": "watson@okaxis",
            "account_type": "Savings",
            "bank_qr_code": self.mock_qr
        }

        response = self.client.post("/api/doctors/bank-details/", payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Verify DB models created except Profile Photo
        self.assertTrue(DoctorPersonalDetails.objects.filter(pk=self.contact_number).exists())
        self.assertFalse(DoctorProfilePhoto.objects.filter(doctor_id=self.contact_number).exists())
        self.assertTrue(DoctorCertification.objects.filter(doctor_id=self.contact_number).exists())
        self.assertTrue(DoctorDocument.objects.filter(doctor_id=self.contact_number).exists())
        self.assertTrue(DoctorBankDetails.objects.filter(doctor_id=self.contact_number).exists())

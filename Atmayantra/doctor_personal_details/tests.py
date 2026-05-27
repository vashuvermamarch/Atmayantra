from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
import base64

from doctor_personal_details.models import DoctorPersonalDetails, DoctorProfilePhoto

class DoctorPersonalDetailsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testdoctoruser",
            phone_number="1234567890",
            email="docuser@example.com",
            password="password123"
        )
        self.doctor_data = {
            "contact_number": "1234567890",
            "full_name": "Dr. John Watson",
            "email": "watson@example.com",
            "gender": "Male",
            "date_of_birth": "1985-05-15",
            "state": "Maharashtra",
            "city": "Mumbai",
            "pincode": "400001",
            "spoken_language": "English, Marathi"
        }
        # A mock profile photo file (GIF format)
        self.mock_photo = SimpleUploadedFile(
            name="profile.gif",
            content=b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif"
        )

    def tearDown(self):
        cache.clear()

    def test_post_onboarding_caches_details_and_photo(self):
        # Onboarding step 1: POST personal details + profile photo
        data = self.doctor_data.copy()
        data["profile_photo"] = self.mock_photo

        # POST is allowed without authentication for onboarding
        response = self.client.post("/api/doctors/personal-details/", data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("temp_id", response.data["data"])

        # Verify details cached
        cached_details = cache.get(f"doctor_personal_details_{self.doctor_data['contact_number']}")
        self.assertIsNotNone(cached_details)
        self.assertEqual(cached_details["full_name"], "Dr. John Watson")
        # Verify photo cached as base64 string
        cached_photo = cache.get(f"doctor_profile_photo_{self.doctor_data['contact_number']}")
        self.assertIsNotNone(cached_photo)
        self.assertTrue(isinstance(cached_photo, str))

    def test_get_personal_details_authenticated(self):
        # Setup doctor in database
        doctor = DoctorPersonalDetails.objects.create(**self.doctor_data)
        photo_b64 = base64.b64encode(self.mock_photo.read()).decode('utf-8')
        self.mock_photo.seek(0)
        DoctorProfilePhoto.objects.create(doctor=doctor, photo_data=photo_b64)

        # Try unauthenticated GET -> Should fail
        response = self.client.get(f"/api/doctors/personal-details/{doctor.contact_number}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticate and try GET -> Should succeed
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/doctors/personal-details/{doctor.contact_number}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["full_name"], "Dr. John Watson")
        self.assertEqual(response.data["data"]["profile_photo"], photo_b64)

    def test_put_updates_details_and_photo_in_database(self):
        # Setup doctor in database
        doctor = DoctorPersonalDetails.objects.create(**self.doctor_data)
        photo_b64 = base64.b64encode(self.mock_photo.read()).decode('utf-8')
        self.mock_photo.seek(0)
        DoctorProfilePhoto.objects.create(doctor=doctor, photo_data=photo_b64)

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Prepare update data with new name and new photo file
        new_photo = SimpleUploadedFile(name="new_profile.jpg", content=b"new_image_data", content_type="image/jpeg")
        update_data = self.doctor_data.copy()
        update_data["full_name"] = "Dr. Watson John"
        update_data["profile_photo"] = new_photo

        response = self.client.put(f"/api/doctors/personal-details/{doctor.contact_number}/", update_data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify updated in DB
        updated_doctor = DoctorPersonalDetails.objects.get(pk=doctor.contact_number)
        self.assertEqual(updated_doctor.full_name, "Dr. Watson John")
        updated_photo = DoctorProfilePhoto.objects.get(doctor=updated_doctor)
        self.assertEqual(updated_photo.photo_data, base64.b64encode(b"new_image_data").decode('utf-8'))

    def test_delete_removes_details_and_photo(self):
        # Setup doctor in database
        doctor = DoctorPersonalDetails.objects.create(**self.doctor_data)
        photo_b64 = base64.b64encode(self.mock_photo.read()).decode('utf-8')
        self.mock_photo.seek(0)
        DoctorProfilePhoto.objects.create(doctor=doctor, photo_data=photo_b64)

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # DELETE request
        response = self.client.delete(f"/api/doctors/personal-details/{doctor.contact_number}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify deleted
        self.assertFalse(DoctorPersonalDetails.objects.filter(pk=doctor.contact_number).exists())
        self.assertFalse(DoctorProfilePhoto.objects.filter(doctor=doctor).exists())

    def test_view_profile_photo_cached(self):
        # 1. Cache the photo data first
        photo_b64 = base64.b64encode(b"dummy_cached_photo_data").decode('utf-8')
        cache.set(f"doctor_profile_photo_{self.doctor_data['contact_number']}", photo_b64, timeout=86400)

        # 2. GET view endpoint
        response = self.client.get(f"/api/doctors/personal-details/{self.doctor_data['contact_number']}/photo/view/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"dummy_cached_photo_data")
        # Since contact_number doesn't end with a known extension, view.py falls back to image/jpeg
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_view_profile_photo_db(self):
        # 1. Create doctor and profile photo in the database
        doctor = DoctorPersonalDetails.objects.create(**self.doctor_data)
        photo_b64 = base64.b64encode(b"dummy_db_photo_data").decode('utf-8')
        DoctorProfilePhoto.objects.create(doctor=doctor, photo_data=photo_b64)

        # 2. GET view endpoint
        response = self.client.get(f"/api/doctors/personal-details/{doctor.contact_number}/photo/view/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"dummy_db_photo_data")
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_view_profile_photo_not_found(self):
        # GET photo view for non-existent doctor/photo
        response = self.client.get("/api/doctors/personal-details/9999999999/photo/view/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_profile_photo_db_authenticated(self):
        # 1. Create doctor and profile photo in DB
        doctor = DoctorPersonalDetails.objects.create(**self.doctor_data)
        # Store with data URI header to test parsing
        photo_b64 = "data:image/gif;base64," + base64.b64encode(b"dummy_gif").decode('utf-8')
        DoctorProfilePhoto.objects.create(doctor=doctor, photo_data=photo_b64)

        # 2. Authenticate
        self.client.force_authenticate(user=self.user)

        # 3. GET download endpoint
        response = self.client.get(f"/api/doctors/personal-details/{doctor.contact_number}/photo/download/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"dummy_gif")
        self.assertEqual(response['Content-Type'], 'image/gif')
        self.assertIn('attachment; filename="profile_1234567890.gif"', response['Content-Disposition'])

    def test_download_profile_photo_unauthenticated(self):
        # Try unauthenticated download
        response = self.client.get(f"/api/doctors/personal-details/{self.doctor_data['contact_number']}/photo/download/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_download_profile_photo_not_found(self):
        # Authenticate
        self.client.force_authenticate(user=self.user)
        # GET download for non-existent doctor
        response = self.client.get("/api/doctors/personal-details/9999999999/photo/download/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_photo_to_cache(self):
        # POST a photo to cache
        data = {
            "contact_number": self.doctor_data["contact_number"],
            "photo_data": self.mock_photo
        }
        # POST doesn't require auth
        response = self.client.post("/api/doctors/personal-details/photo/", data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Verify cached
        cached_photo = cache.get(f"doctor_profile_photo_{self.doctor_data['contact_number']}")
        self.assertIsNotNone(cached_photo)
        self.assertTrue(isinstance(cached_photo, str))

    def test_put_photo_to_cache_authenticated(self):
        # PUT updates photo in cache, requires authentication
        self.client.force_authenticate(user=self.user)
        data = {
            "photo_data": self.mock_photo
        }
        response = self.client.put(
            f"/api/doctors/personal-details/photo/{self.doctor_data['contact_number']}/",
            data,
            format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    def test_delete_photo_from_db_authenticated(self):
        # 1. Create doctor and photo in DB
        doctor = DoctorPersonalDetails.objects.create(**self.doctor_data)
        photo_b64 = base64.b64encode(b"some_data").decode('utf-8')
        DoctorProfilePhoto.objects.create(doctor=doctor, photo_data=photo_b64)

        # 2. Authenticate
        self.client.force_authenticate(user=self.user)

        # 3. DELETE request
        data = {"contact_number": doctor.contact_number}
        response = self.client.delete("/api/doctors/personal-details/photo/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Verify photo is deleted from DB
        self.assertFalse(DoctorProfilePhoto.objects.filter(doctor=doctor).exists())

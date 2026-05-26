from django.contrib.auth import get_user_model
from django.test import TestCase


class UserModelTests(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            phone_number="1234567890",
            email="testuser@example.com",
            password="testpassword123"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.phone_number, "1234567890")
        self.assertEqual(user.email, "testuser@example.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_verified)

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username="adminuser",
            phone_number="0987654321",
            email="adminuser@example.com",
            password="adminpassword123"
        )
        self.assertEqual(admin_user.username, "adminuser")
        self.assertEqual(admin_user.phone_number, "0987654321")
        self.assertEqual(admin_user.email, "adminuser@example.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_verified)


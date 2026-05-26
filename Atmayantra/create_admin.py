import os

import django

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Atmayantra.settings')
django.setup()

from admin_auth.models import AdminUser
from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin():
    # Fetch credentials from environment variables with defaults
    username = os.getenv('ADMIN_USERNAME', 'admin')
    password = os.getenv('ADMIN_PASSWORD', 'admin')
    email = os.getenv('ADMIN_EMAIL', 'admin@atmayantra.com')
    phone_number = os.getenv('ADMIN_PHONE', '0000000000')

    # 1. Create Superuser for Django Admin (/admin/)
    if not User.objects.filter(username=username).exists():
        print(f"Creating superuser: {username}")
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
            is_active=True
        )
    else:
        print(f"Superuser {username} already exists. Updating password.")
        u = User.objects.get(username=username)
        u.set_password(password)
        u.save()

    # 2. Create entry in custom AdminUser table for custom admin auth
    if not AdminUser.objects.filter(contact_number=phone_number).exists():
        print(f"Creating AdminUser entry: {phone_number}")
        AdminUser.objects.create(
            contact_number=phone_number,
            name='System Admin',
            email=email,
            password=password, # Note: if your system hashes this, you might need to hash it here
            is_verified=True
        )
    else:
        print(f"AdminUser entry {phone_number} already exists. Updating details.")
        a = AdminUser.objects.get(contact_number=phone_number)
        a.password = password
        a.is_verified = True
        a.save()

if __name__ == '__main__':
    create_admin()

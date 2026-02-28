import secrets
import string
from django.core.mail import send_mail
from django.conf import settings


def generate_manager_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def send_manager_credentials(email, username, employee_id, contact_number, password):

    try:
        send_mail(
            subject="Manager Account Created",
            message=f"""
Manager Account Created

Username: {username}
Employee ID: {employee_id}
Contact Number: {contact_number}
Password: {password}
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
    except Exception as e:
        # Log the error or handle it as needed, but don't crash the onboarding process
        print(f"SMTP Error: {e}")
        return False

    return True

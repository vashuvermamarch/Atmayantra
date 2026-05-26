import secrets
import string
import traceback


def generate_manager_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def send_manager_credentials(email, username, employee_id, contact_number, password):
    """
    Sends manager credentials via Gmail SMTP.
    Works on both local and Azure (SMTP-friendly platforms).
    """
    from django.conf import settings
    from django.core.mail import send_mail

    subject = "Manager Account Created"
    message = f"""Manager Account Created

Username: {username}
Employee ID: {employee_id}
Contact Number: {contact_number}
Password: {password}
"""

    try:
        print(f"DEBUG: Sending email via SMTP to {email}")
        print(f"DEBUG: SMTP Config - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}")

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        print(f"DEBUG: Email sent SUCCESSFULLY to {email}")
        return True

    except Exception as e:
        print(f"CRITICAL: SMTP Error to {email}: {str(e)}")
        print(traceback.format_exc())
        return False

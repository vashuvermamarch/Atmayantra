import secrets
import string


def generate_manager_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def send_manager_credentials(email, username, employee_id, contact_number, password):
    """
    Sends manager credentials via email.
    Sends synchronously with a timeout to prevent:
    1. Gunicorn killing daemon threads before email completes
    2. Infinite SMTP hangs blocking the response
    """
    from django.core.mail import send_mail
    from django.conf import settings
    import traceback

    subject = "Manager Account Created"
    message = f"""
Manager Account Created

Username: {username}
Employee ID: {employee_id}
Contact Number: {contact_number}
Password: {password}
"""

    try:
        # --- DEBUG LOGS FOR RENDER ---
        print(f"DEBUG: STARTing email process for {email}")
        print(f"DEBUG: SMTP Config - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}, TLS: {settings.EMAIL_USE_TLS}, SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}")
        print(f"DEBUG: SMTP User: {settings.EMAIL_HOST_USER}")
        print(f"DEBUG: From Email: {settings.DEFAULT_FROM_EMAIL}")

        if not settings.EMAIL_HOST_PASSWORD:
            print("CRITICAL: EMAIL_HOST_PASSWORD is EMPTY or NONE!")
        else:
            print(f"DEBUG: EMAIL_HOST_PASSWORD is present (Length: {len(settings.EMAIL_HOST_PASSWORD)})")

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
        print("DEBUG: Full SMTP Traceback:")
        print(traceback.format_exc())
        return False

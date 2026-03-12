import secrets
import string
import traceback


def generate_manager_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def _send_via_resend(email, subject, message):
    """Send email via Resend HTTP API (works on Render where SMTP is blocked)."""
    import requests
    from django.conf import settings

    api_key = getattr(settings, 'RESEND_API_KEY', None)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

    if not api_key:
        print("CRITICAL: RESEND_API_KEY is not set! Cannot send email via Resend.")
        return False

    print(f"DEBUG: Sending email via Resend API to {email}")

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "from": from_email,
            "to": [email],
            "subject": subject,
            "text": message
        },
        timeout=30
    )

    if response.status_code == 200:
        print(f"DEBUG: Resend email sent SUCCESSFULLY to {email}")
        return True
    else:
        print(f"CRITICAL: Resend API Error ({response.status_code}): {response.text}")
        return False


def _send_via_smtp(email, subject, message):
    """Send email via Django's built-in SMTP (works locally)."""
    from django.core.mail import send_mail
    from django.conf import settings

    print(f"DEBUG: Sending email via SMTP to {email}")
    print(f"DEBUG: SMTP Config - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}")

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False
    )
    print(f"DEBUG: SMTP email sent SUCCESSFULLY to {email}")
    return True


def send_manager_credentials(email, username, employee_id, contact_number, password):
    """
    Sends manager credentials via email.
    Uses Resend API if RESEND_API_KEY is set (for Render),
    falls back to SMTP (for local development).
    Never crashes — returns False on failure so manager creation still completes.
    """
    from django.conf import settings

    subject = "Manager Account Created"
    message = f"""Manager Account Created

Username: {username}
Employee ID: {employee_id}
Contact Number: {contact_number}
Password: {password}
"""

    try:
        # Use Resend API if key is configured (for Render/production)
        if getattr(settings, 'RESEND_API_KEY', None):
            return _send_via_resend(email, subject, message)
        else:
            # Fall back to SMTP (for local development)
            return _send_via_smtp(email, subject, message)

    except Exception as e:
        print(f"CRITICAL: Email Error to {email}: {str(e)}")
        print(traceback.format_exc())
        return False

import secrets
import string


def generate_manager_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


import threading
import traceback

def _send_email_async(email, subject, message):
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        import traceback
        
        # --- DEBUG LOGS FOR RENDER ---
        print(f"DEBUG: STARTing background email process for {email}")
        print(f"DEBUG: SMTP Config - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}, TLS: {settings.EMAIL_USE_TLS}, SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}")
        print(f"DEBUG: SMTP User: {settings.EMAIL_HOST_USER}")
        print(f"DEBUG: From Email: {settings.DEFAULT_FROM_EMAIL}")
        
        # Verify password exists (but don't log it!)
        if not settings.EMAIL_HOST_PASSWORD:
            print("CRITICAL: EMAIL_HOST_PASSWORD is EMPTY or NONE in environment!")
        else:
            print(f"DEBUG: EMAIL_HOST_PASSWORD is present (Length: {len(settings.EMAIL_HOST_PASSWORD)})")

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        print(f"DEBUG: Background email sent successfully to {email}")
    except Exception as e:
        import traceback
        print(f"CRITICAL: SMTP Error to {email}: {str(e)}")
        print("DEBUG: Full SMTP Traceback:")
        print(traceback.format_exc())

def send_manager_credentials(email, username, employee_id, contact_number, password):
    subject = "Manager Account Created"
    message = f"""
Manager Account Created

Username: {username}
Employee ID: {employee_id}
Contact Number: {contact_number}
Password: {password}
"""
    # Send email in a separate thread so it doesn't block the request and trigger Gunicorn timeout
    email_thread = threading.Thread(
        target=_send_email_async,
        args=(email, subject, message)
    )
    email_thread.daemon = True  # Thread will exit when the main process exits
    email_thread.start()
    
    return True

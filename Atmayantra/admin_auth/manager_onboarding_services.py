import secrets
import string


def generate_manager_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


import threading

def _send_email_async(email, subject, message):
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True
        )
    except BaseException as e:
        print(f"Background SMTP/Process Error: {e}")

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

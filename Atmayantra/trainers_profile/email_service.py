from django.core.mail import send_mail
from django.conf import settings


def send_trainer_status_email(trainer, status_type):
    """
    status_type: approved | rejected | blocked | activated
    """

    subject_map = {
        'approved': 'Trainer Approved - Atmayantra',
        'rejected': 'Trainer Application Rejected - Atmayantra',
        'blocked': 'Trainer Profile Blocked - Atmayantra',
        'activated': 'Trainer Profile Activated - Atmayantra',
    }

    message_map = {
        'approved': f"Hello {trainer.full_name},\n\nYour profile has been approved successfully.\n\nTeam Atmayantra",
        'rejected': f"Hello {trainer.full_name},\n\nYour profile has been rejected. Please contact support for more details.\n\nTeam Atmayantra",
        'blocked': f"Hello {trainer.full_name},\n\nYour profile has been blocked by admin. Please contact support.\n\nTeam Atmayantra",
        'activated': f"Hello {trainer.full_name},\n\nYour profile has been activated again.\n\nTeam Atmayantra",
    }

    subject = subject_map.get(status_type, "Trainer Notification - Atmayantra")
    message = message_map.get(status_type, "Hello, Status updated.")

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [trainer.email],
        fail_silently=False
    )
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import Notification, Severity

logger = logging.getLogger(__name__)


def notify(
    user,
    *,
    kind: str,
    title: str,
    body: str,
    severity: str = Severity.INFO,
    payload: dict | None = None,
    generation=None,
    send_email: bool = True,
) -> Notification:
    notification = Notification.objects.create(
        user=user,
        kind=kind,
        title=title,
        body=body,
        severity=severity,
        payload=payload or {},
        generation=generation,
    )

    if send_email and user.email:
        from .tasks import send_notification_email

        send_notification_email.delay(notification.pk)

    return notification


def deliver_email(notification: Notification) -> bool:
    user = notification.user
    if not user.email:
        return False
    if notification.emailed_at:
        return False

    nombre = user.first_name or user.username
    cuerpo = (
        f"Hola {nombre}:\n\n"
        f"{notification.body}\n\n"
        f"Puedes verlo en {settings.SITE_URL}{reverse('notification_list')}\n\n"
        "— FitUp"
    )

    send_mail(
        subject=notification.title,
        message=cuerpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    notification.emailed_at = timezone.now()
    notification.save(update_fields=["emailed_at"])
    return True


def unread_count(user) -> int:
    return Notification.objects.filter(user=user, is_read=False).count()

import logging

from celery import shared_task

from .models import Notification
from .services import deliver_email

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_notification_email(self, notification_id: int) -> str:
    try:
        notification = Notification.objects.get(pk=notification_id)
    except Notification.DoesNotExist:
        return "missing"

    return "sent" if deliver_email(notification) else "skipped"

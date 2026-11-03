import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.bodyweight.models import BodyWeightEntry

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BodyWeightEntry, dispatch_uid="aiassist_analyze_bodyweight")
def on_bodyweight_saved(sender, instance, created, **kwargs):
    from .tasks import analyze_new_bodyweight

    try:
        analyze_new_bodyweight.delay(instance.pk)
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo encolar el análisis de peso: %s", exc)

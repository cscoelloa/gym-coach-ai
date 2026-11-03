from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone

from apps.notifications import push

from .models import WorkoutSession

TOLERANCIA = timedelta(seconds=2)

CADUCIDAD = timedelta(minutes=2)


@shared_task(bind=True, ignore_result=True)
def avisar_fin_del_descanso(self, sesion_id: int, fin_iso: str, reintento: bool = False) -> str:
    fin = datetime.fromisoformat(fin_iso)
    ahora = timezone.now()

    if ahora < fin - TOLERANCIA:
        if self.request.is_eager or reintento:
            return "temprano"
        self.apply_async((sesion_id, fin_iso), {"reintento": True}, eta=fin)
        return "reprogramado"

    if ahora > fin + CADUCIDAD:
        return "caducado"

    actualizadas = WorkoutSession.objects.filter(
        pk=sesion_id, rest_ends_at=fin, finished_at__isnull=True
    ).update(rest_ends_at=None, rest_seconds=None)
    if not actualizadas:
        return "cambiado"

    user_id = WorkoutSession.objects.values_list("user_id", flat=True).get(pk=sesion_id)
    push.enviar(
        user_id,
        {
            "tipo": "descanso",
            "titulo": "Descanso terminado",
            "cuerpo": "A por la siguiente serie.",
            "url": f"/entrenamientos/{sesion_id}/",
            "tag": f"descanso-{sesion_id}",
        },
        ttl=60,
        tema=f"descanso-{sesion_id}",
    )
    return "enviado"

from datetime import timedelta

from django.db import transaction

from apps.notifications import push
from apps.notifications.models import SuscripcionPush

from . import focus

ALARGAR_SEGUNDOS = 30

MAXIMO_SEGUNDOS = 30 * 60

CAMPOS = ["rest_ends_at", "rest_seconds"]


def tras_registrar(sesion, serie, ahora) -> None:
    segundos = focus.descanso_tras_registrar(sesion, serie)
    if segundos:
        sesion.rest_ends_at = ahora + timedelta(seconds=segundos)
        sesion.rest_seconds = segundos
    else:
        sesion.rest_ends_at = None
        sesion.rest_seconds = None
    sesion.save(update_fields=CAMPOS)
    _programar_aviso(sesion)


def alargar(sesion, ahora) -> None:
    if focus.estado_del_descanso(sesion, ahora) is None:
        return
    total = min((sesion.rest_seconds or 0) + ALARGAR_SEGUNDOS, MAXIMO_SEGUNDOS)
    sesion.rest_ends_at += timedelta(seconds=total - (sesion.rest_seconds or 0))
    sesion.rest_seconds = total
    sesion.save(update_fields=CAMPOS)
    _programar_aviso(sesion)


def saltar(sesion) -> None:
    sesion.rest_ends_at = None
    sesion.rest_seconds = None
    sesion.save(update_fields=CAMPOS)


def limpiar(sesion) -> None:
    sesion.rest_ends_at = None
    sesion.rest_seconds = None


def _programar_aviso(sesion) -> None:
    if sesion.rest_ends_at is None or not push.activo():
        return
    if not SuscripcionPush.objects.filter(user_id=sesion.user_id).exists():
        return

    from .tasks import avisar_fin_del_descanso

    fin = sesion.rest_ends_at
    transaction.on_commit(
        lambda: avisar_fin_del_descanso.apply_async(
            (sesion.pk, fin.isoformat()), eta=fin, retry_policy={"max_retries": 1}
        ),
        robust=True,
    )

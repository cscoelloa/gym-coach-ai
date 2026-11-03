import json
import logging
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests
from django.conf import settings
from pywebpush import WebPushException, webpush

from .models import SuscripcionPush

logger = logging.getLogger(__name__)


def activo() -> bool:
    return bool(
        settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_SUBJECT
    )


def clave_publica() -> str | None:
    return settings.VAPID_PUBLIC_KEY if activo() else None


def servicio_permitido(endpoint: str) -> bool:
    partes = urlsplit(endpoint)
    if partes.scheme != "https" or not partes.hostname:
        return False
    host = partes.hostname.lower()
    return any(
        host == permitido or (permitido.startswith(".") and host.endswith(permitido))
        for permitido in settings.AVISOS_PUSH_HOSTS
    )


@dataclass
class Resultado:
    enviados: int = 0
    caducadas: int = 0
    fallidas: int = 0


def enviar(user_id: int, datos: dict, *, ttl: int, tema: str | None = None) -> Resultado:
    resultado = Resultado()
    if not activo():
        return resultado

    cabeceras = {"Urgency": "high"}
    if tema:
        cabeceras["Topic"] = tema

    for suscripcion in SuscripcionPush.objects.filter(user_id=user_id):
        try:
            webpush(
                subscription_info={
                    "endpoint": suscripcion.endpoint,
                    "keys": {"p256dh": suscripcion.p256dh, "auth": suscripcion.auth},
                },
                data=json.dumps(datos),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                ttl=ttl,
                headers=dict(cabeceras),
                timeout=10,
            )
            resultado.enviados += 1
        except WebPushException as error:
            estado = getattr(error.response, "status_code", None)
            if estado in (404, 410):
                suscripcion.delete()
                resultado.caducadas += 1
            else:
                resultado.fallidas += 1
                logger.warning(
                    "Aviso push fallido: suscripción %s, estado %s", suscripcion.pk, estado
                )
        except requests.RequestException:
            resultado.fallidas += 1
            logger.warning("Aviso push sin respuesta: suscripción %s", suscripcion.pk)

    return resultado

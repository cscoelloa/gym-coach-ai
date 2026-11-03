from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.notifications.models import SuscripcionPush
from apps.workouts import descanso, tasks
from apps.workouts.models import WorkoutSession

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def sesion():
    ana = User.objects.create_user("ana", password="Contrasena-Larga-Tarea-1")
    return WorkoutSession.objects.create(user=ana, date=timezone.localdate())


def con_descanso(sesion, fin):
    sesion.rest_ends_at = fin
    sesion.rest_seconds = 90
    sesion.save()
    return fin


def ejecutar(sesion, fin):
    tarea = tasks.avisar_fin_del_descanso
    with mock.patch.object(tasks.push, "enviar") as enviar:
        tarea.request.is_eager = False
        resultado = tarea.run(sesion.pk, fin.isoformat())
    return resultado, enviar


def test_a_su_hora_avisa_y_vacia_el_descanso(sesion):
    fin = con_descanso(sesion, timezone.now())

    resultado, enviar = ejecutar(sesion, fin)

    assert resultado == "enviado"
    enviar.assert_called_once()
    sesion.refresh_from_db()
    assert sesion.rest_ends_at is None


def test_el_mensaje_no_lleva_datos_de_nadie(sesion):
    fin = con_descanso(sesion, timezone.now())

    _, enviar = ejecutar(sesion, fin)

    datos = enviar.call_args.args[1]
    assert set(datos) == {"tipo", "titulo", "cuerpo", "url", "tag"}
    assert "kg" not in str(datos)


@pytest.mark.parametrize("cambio", ["saltado", "alargado", "terminado"])
def test_si_el_descanso_cambio_no_avisa(sesion, cambio):
    fin = con_descanso(sesion, timezone.now())
    if cambio == "saltado":
        sesion.rest_ends_at = None
    elif cambio == "alargado":
        sesion.rest_ends_at = fin + timedelta(seconds=30)
    else:
        sesion.finished_at = timezone.now()
    sesion.save()

    resultado, enviar = ejecutar(sesion, fin)

    assert resultado == "cambiado"
    enviar.assert_not_called()


def test_dos_veces_avisa_una(sesion):
    fin = con_descanso(sesion, timezone.now())

    ejecutar(sesion, fin)
    resultado, enviar = ejecutar(sesion, fin)

    assert resultado == "cambiado"
    enviar.assert_not_called()


def test_en_modo_eager_antes_de_tiempo_no_hace_nada(sesion):
    fin = con_descanso(sesion, timezone.now() + timedelta(seconds=90))
    tarea = tasks.avisar_fin_del_descanso

    with mock.patch.object(tasks.push, "enviar") as enviar:
        resultado = tarea.apply(args=(sesion.pk, fin.isoformat())).get()

    assert resultado == "temprano"
    enviar.assert_not_called()
    sesion.refresh_from_db()
    assert sesion.rest_ends_at == fin


def test_muy_tarde_ya_no_avisa(sesion):
    fin = con_descanso(sesion, timezone.now() - timedelta(minutes=5))

    resultado, enviar = ejecutar(sesion, fin)

    assert resultado == "caducado"
    enviar.assert_not_called()


class TestProgramarElAviso(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana", password="Contrasena-Larga-Tarea-1")
        self.sesion = WorkoutSession.objects.create(user=self.ana, date=timezone.localdate())
        self.sesion.rest_ends_at = timezone.now() + timedelta(seconds=90)
        self.sesion.rest_seconds = 90

    def programar(self):
        with mock.patch.object(tasks.avisar_fin_del_descanso, "apply_async") as encolar:
            with self.captureOnCommitCallbacks(execute=True):
                descanso._programar_aviso(self.sesion)
        return encolar

    def test_con_suscripcion_y_claves_se_encola_a_su_hora(self):
        SuscripcionPush.objects.create(
            user=self.ana, endpoint="https://fcm.googleapis.com/x", p256dh="p", auth="a"
        )
        with self.settings(VAPID_PUBLIC_KEY="a", VAPID_PRIVATE_KEY="b", VAPID_SUBJECT="mailto:c"):
            encolar = self.programar()

        encolar.assert_called_once()
        assert encolar.call_args.kwargs["eta"] == self.sesion.rest_ends_at

    def test_sin_suscripcion_no_se_encola(self):
        with self.settings(VAPID_PUBLIC_KEY="a", VAPID_PRIVATE_KEY="b", VAPID_SUBJECT="mailto:c"):
            encolar = self.programar()

        encolar.assert_not_called()

    def test_sin_claves_no_se_encola(self):
        SuscripcionPush.objects.create(
            user=self.ana, endpoint="https://fcm.googleapis.com/x", p256dh="p", auth="a"
        )
        with self.settings(VAPID_PUBLIC_KEY=""):
            encolar = self.programar()

        encolar.assert_not_called()

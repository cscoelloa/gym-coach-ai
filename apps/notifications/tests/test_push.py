import base64
import logging
from unittest import mock

import pytest
import requests
from django.contrib.auth import get_user_model
from django.urls import reverse
from pywebpush import WebPushException
from rest_framework.test import APIClient

from apps.notifications import push
from apps.notifications.models import SuscripcionPush

pytestmark = pytest.mark.django_db

User = get_user_model()

P256DH = base64.urlsafe_b64encode(b"\x04" + b"\x01" * 64).decode().rstrip("=")
AUTH = base64.urlsafe_b64encode(b"\x02" * 16).decode().rstrip("=")
ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123"


@pytest.fixture
def vapid(settings):
    settings.VAPID_PUBLIC_KEY = "clave-publica-de-prueba"
    settings.VAPID_PRIVATE_KEY = "clave-privada-que-no-sale"
    settings.VAPID_SUBJECT = "mailto:equipo@ejemplo.com"


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-Push-1")


@pytest.fixture
def beto():
    return User.objects.create_user("beto", password="Contrasena-Larga-Push-1")


@pytest.fixture
def api(ana):
    cliente = APIClient()
    cliente.force_login(ana)
    return cliente


def suscribir(api, endpoint=ENDPOINT, p256dh=P256DH, auth=AUTH):
    return api.post(
        reverse("api-avisos-suscripcion"),
        {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}},
        format="json",
    )


class TestLaClave:
    def test_sin_configurar_el_aviso_esta_apagado(self, api, settings):
        settings.VAPID_PUBLIC_KEY = ""

        assert api.get(reverse("api-avisos-clave")).json() == {"activo": False, "clave": None}

    def test_con_configurar_da_la_publica_y_nunca_la_privada(self, api, vapid):
        respuesta = api.get(reverse("api-avisos-clave"))

        assert respuesta.json() == {"activo": True, "clave": "clave-publica-de-prueba"}
        assert b"clave-privada-que-no-sale" not in respuesta.content


class TestSuscribirse:
    def test_guarda_la_suscripcion_del_navegador(self, api, ana, vapid):
        assert suscribir(api).status_code == 204

        guardada = SuscripcionPush.objects.get()
        assert guardada.user == ana
        assert guardada.endpoint == ENDPOINT

    def test_sin_claves_vapid_no_se_acepta(self, api):
        assert suscribir(api).status_code == 409
        assert not SuscripcionPush.objects.exists()

    @pytest.mark.parametrize(
        "endpoint",
        [
            "http://fcm.googleapis.com/fcm/send/abc",
            "https://169.254.169.254/latest/meta-data/",
            "https://localhost:8000/admin/",
            "https://fcm.googleapis.com.atacante.com/x",
        ],
    )
    def test_solo_servicios_de_push_conocidos(self, api, vapid, endpoint):
        assert suscribir(api, endpoint=endpoint).status_code == 400
        assert not SuscripcionPush.objects.exists()

    def test_un_subdominio_de_un_servicio_permitido_vale(self, api, vapid):
        assert suscribir(api, endpoint="https://api.push.apple.com/3/device/x").status_code == 204

    @pytest.mark.parametrize("p256dh, auth", [("no-es-base64-valido!!", AUTH), (P256DH, "corta")])
    def test_claves_mal_formadas_se_rechazan(self, api, vapid, p256dh, auth):
        assert suscribir(api, p256dh=p256dh, auth=auth).status_code == 400

    def test_el_mismo_navegador_pasa_a_quien_entra_despues(self, api, vapid, beto):
        SuscripcionPush.objects.create(user=beto, endpoint=ENDPOINT, p256dh=P256DH, auth=AUTH)

        suscribir(api)

        assert SuscripcionPush.objects.get().user.username == "ana"

    def test_hay_un_tope_por_persona(self, api, ana, vapid):
        for numero in range(12):
            suscribir(api, endpoint=f"https://fcm.googleapis.com/fcm/send/{numero}")

        assert SuscripcionPush.objects.filter(user=ana).count() == 10

    def test_sin_token_csrf_no_se_suscribe(self, ana, vapid):
        cliente = APIClient(enforce_csrf_checks=True)
        cliente.force_login(ana)

        assert suscribir(cliente).status_code == 403


class TestDarseDeBaja:
    def test_borra_la_de_este_navegador(self, api, ana, vapid):
        suscribir(api)

        respuesta = api.delete(
            reverse("api-avisos-suscripcion"), {"endpoint": ENDPOINT}, format="json"
        )

        assert respuesta.status_code == 204
        assert not SuscripcionPush.objects.exists()

    def test_no_borra_la_de_otra_persona_ni_dice_si_existe(self, api, beto):
        SuscripcionPush.objects.create(user=beto, endpoint=ENDPOINT, p256dh=P256DH, auth=AUTH)

        respuesta = api.delete(
            reverse("api-avisos-suscripcion"), {"endpoint": ENDPOINT}, format="json"
        )

        assert respuesta.status_code == 204
        assert SuscripcionPush.objects.filter(user=beto).exists()

    def test_borrar_la_cuenta_se_las_lleva(self, ana):
        SuscripcionPush.objects.create(user=ana, endpoint=ENDPOINT, p256dh=P256DH, auth=AUTH)

        ana.delete()

        assert not SuscripcionPush.objects.exists()


class TestEnviar:
    @pytest.fixture
    def suscrita(self, ana):
        return SuscripcionPush.objects.create(
            user=ana, endpoint=ENDPOINT, p256dh=P256DH, auth=AUTH
        )

    def test_sin_configurar_no_manda_nada(self, ana, suscrita, settings):
        settings.VAPID_PRIVATE_KEY = ""
        with mock.patch.object(push, "webpush") as webpush:
            push.enviar(ana.pk, {"titulo": "x"}, ttl=60)

        webpush.assert_not_called()

    def test_manda_a_cada_navegador_con_su_firma(self, ana, suscrita, vapid):
        SuscripcionPush.objects.create(
            user=ana, endpoint="https://updates.push.services.mozilla.com/wpush/v2/x",
            p256dh=P256DH, auth=AUTH,
        )
        with mock.patch.object(push, "webpush") as webpush:
            resultado = push.enviar(ana.pk, {"titulo": "x"}, ttl=60, tema="descanso-1")

        assert resultado.enviados == 2
        claims = [llamada.kwargs["vapid_claims"] for llamada in webpush.call_args_list]
        assert claims[0] is not claims[1]
        assert webpush.call_args.kwargs["headers"]["Topic"] == "descanso-1"

    @pytest.mark.parametrize("estado", [404, 410])
    def test_una_suscripcion_muerta_se_borra(self, ana, suscrita, vapid, estado):
        error = WebPushException("gone", response=mock.Mock(status_code=estado))
        with mock.patch.object(push, "webpush", side_effect=error):
            resultado = push.enviar(ana.pk, {"titulo": "x"}, ttl=60)

        assert resultado.caducadas == 1
        assert not SuscripcionPush.objects.exists()

    def test_un_fallo_pasajero_la_conserva_y_no_loguea_el_endpoint(
        self, ana, suscrita, vapid, caplog
    ):
        error = WebPushException(
            f"Push failed: 500 {ENDPOINT}", response=mock.Mock(status_code=500)
        )
        with (
            caplog.at_level(logging.WARNING),
            mock.patch.object(push, "webpush", side_effect=error),
        ):
            resultado = push.enviar(ana.pk, {"titulo": "x"}, ttl=60)

        assert resultado.fallidas == 1
        assert SuscripcionPush.objects.exists()
        assert ENDPOINT not in caplog.text
        assert P256DH not in caplog.text

    def test_sin_respuesta_no_revienta(self, ana, suscrita, vapid):
        with mock.patch.object(push, "webpush", side_effect=requests.Timeout()):
            assert push.enviar(ana.pk, {"titulo": "x"}, ttl=60).fallidas == 1

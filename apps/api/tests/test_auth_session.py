from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

User = get_user_model()
PASSWORD = "Contrasena-Larga-Api-1"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def api_con_csrf():
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def ana():
    return User.objects.create_user(
        "ana",
        password=PASSWORD,
        email="ana@example.com",
        first_name="Ana",
        birth_date=date(1994, 3, 2),
        height_cm=168,
        injuries_notes="Hombro derecho",
    )


class TestConsultarLaSesion:
    def test_sin_sesion_responde_401(self, api):
        respuesta = api.get(reverse("api-session"))

        assert respuesta.status_code == 401

    def test_con_sesion_dice_quién_eres(self, api, ana):
        api.force_login(ana)

        datos = api.get(reverse("api-session")).json()

        assert datos["username"] == "ana"
        assert datos["first_name"] == "Ana"
        assert datos["is_staff"] is False

    def test_no_devuelve_datos_de_salud(self, api, ana):
        api.force_login(ana)

        datos = api.get(reverse("api-session")).json()

        prohibidos = {
            "birth_date", "height_cm", "injuries_notes", "sex", "target_weight_kg", "age",
        }
        colados = prohibidos & set(datos)
        assert not colados, f"datos de salud en la respuesta de sesión: {colados}"

    def test_deja_puesta_la_cookie_csrf(self, api):
        respuesta = api.get(reverse("api-session"))

        assert "csrftoken" in respuesta.cookies


class TestEntrar:
    def test_abre_sesion(self, api, ana):
        respuesta = api.post(
            reverse("api-session"), {"username": "ana", "password": PASSWORD}, format="json"
        )

        assert respuesta.status_code == 200
        assert respuesta.json()["usuario"]["username"] == "ana"
        assert api.get(reverse("api-session")).status_code == 200

    def test_sin_destino_va_a_inicio(self, api, ana):
        respuesta = api.post(
            reverse("api-session"), {"username": "ana", "password": PASSWORD}, format="json"
        )

        assert respuesta.json()["redirect"] == "/"

    def test_respeta_el_destino_previo(self, api, ana):
        respuesta = api.post(
            reverse("api-session"),
            {"username": "ana", "password": PASSWORD, "next": "/plan/"},
            format="json",
        )

        assert respuesta.json()["redirect"] == "/plan/"

    @pytest.mark.parametrize(
        "destino",
        [
            "https://sitio-falso.example/",
            "//sitio-falso.example/",
            "http://otro-host/plan/",
        ],
    )
    def test_un_destino_de_otro_host_se_descarta(self, api, ana, destino):
        respuesta = api.post(
            reverse("api-session"),
            {"username": "ana", "password": PASSWORD, "next": destino},
            format="json",
        )

        assert respuesta.json()["redirect"] == "/"

    @pytest.mark.parametrize(
        "usuario,clave",
        [("ana", "la-que-no-es"), ("no-existe", PASSWORD)],
    )
    def test_el_mensaje_no_distingue_si_la_cuenta_existe(self, api, ana, usuario, clave):
        respuesta = api.post(
            reverse("api-session"), {"username": usuario, "password": clave}, format="json"
        )

        assert respuesta.status_code == 400
        assert respuesta.json()["detail"] == "Usuario o contraseña incorrectos."

    def test_sin_token_csrf_no_se_entra(self, api_con_csrf, ana):
        respuesta = api_con_csrf.post(
            reverse("api-session"), {"username": "ana", "password": PASSWORD}, format="json"
        )

        assert respuesta.status_code == 403

    def test_con_token_csrf_sí(self, api_con_csrf, ana):
        api_con_csrf.get(reverse("api-session"))
        token = api_con_csrf.cookies["csrftoken"].value

        respuesta = api_con_csrf.post(
            reverse("api-session"),
            {"username": "ana", "password": PASSWORD},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        assert respuesta.status_code == 200


class TestElBloqueoPorIntentos:
    def test_tras_cinco_fallos_la_cuenta_queda_bloqueada(self, api, ana, settings):
        for _ in range(settings.AXES_FAILURE_LIMIT):
            api.post(
                reverse("api-session"),
                {"username": "ana", "password": "la-que-no-es"},
                format="json",
            )

        respuesta = api.post(
            reverse("api-session"), {"username": "ana", "password": PASSWORD}, format="json"
        )

        assert respuesta.status_code == 403
        assert "bloqueada" in respuesta.json()["detail"]


class TestSalir:
    def test_cierra_la_sesion(self, api, ana):
        api.force_login(ana)

        assert api.delete(reverse("api-session")).status_code == 204
        assert api.get(reverse("api-session")).status_code == 401

    def test_sin_sesion_tambien_responde_bien(self, api):
        assert api.delete(reverse("api-session")).status_code == 204


class TestRegistrarse:
    def test_crea_la_cuenta_y_deja_dentro(self, api):
        respuesta = api.post(
            reverse("api-registro"),
            {
                "username": "carla",
                "email": "carla@example.com",
                "password": "Contrasena-Larga-1",
                "password2": "Contrasena-Larga-1",
            },
            format="json",
        )

        assert respuesta.status_code == 201
        assert User.objects.filter(username="carla").exists()
        assert api.get(reverse("api-session")).json()["username"] == "carla"

    def test_lleva_al_perfil_y_no_a_inicio(self, api):
        respuesta = api.post(
            reverse("api-registro"),
            {
                "username": "carla", "email": "c@example.com",
                "password": "Contrasena-Larga-1", "password2": "Contrasena-Larga-1",
            },
            format="json",
        )

        assert respuesta.json()["redirect"] == "/perfil/"

    def test_las_dos_contrasenas_tienen_que_coincidir(self, api):
        respuesta = api.post(
            reverse("api-registro"),
            {
                "username": "carla", "email": "c@example.com",
                "password": "Contrasena-Larga-1", "password2": "Otra-Contrasena-2",
            },
            format="json",
        )

        assert respuesta.status_code == 400
        assert "password2" in respuesta.json()

    @pytest.mark.parametrize(
        "clave,motivo",
        [
            ("corta1", "por debajo del mínimo de 10"),
            ("12345678901", "solo numérica"),
            ("password123", "demasiado común"),
        ],
    )
    def test_aplica_los_validadores_de_contrasena(self, api, clave, motivo):
        respuesta = api.post(
            reverse("api-registro"),
            {"username": "carla", "email": "c@example.com", "password": clave, "password2": clave},
            format="json",
        )

        assert respuesta.status_code == 400, motivo
        assert "password" in respuesta.json()

    def test_el_nombre_de_usuario_no_se_repite(self, api, ana):
        respuesta = api.post(
            reverse("api-registro"),
            {
                "username": "ana", "email": "otra@example.com",
                "password": "Contrasena-Larga-1", "password2": "Contrasena-Larga-1",
            },
            format="json",
        )

        assert respuesta.status_code == 400
        assert "username" in respuesta.json()

    def test_la_contrasena_no_vuelve_en_la_respuesta(self, api):
        respuesta = api.post(
            reverse("api-registro"),
            {
                "username": "carla", "email": "c@example.com",
                "password": "Contrasena-Larga-1", "password2": "Contrasena-Larga-1",
            },
            format="json",
        )

        assert "password" not in str(respuesta.json())


class TestCambiarLaContrasena:
    def test_la_cambia_sin_echar_de_la_sesion(self, api, ana):
        api.force_login(ana)

        respuesta = api.post(
            reverse("api-password"),
            {"actual": PASSWORD, "nueva": "Otra-Contrasena-Larga-2"},
            format="json",
        )

        assert respuesta.status_code == 204
        assert api.get(reverse("api-session")).status_code == 200
        ana.refresh_from_db()
        assert ana.check_password("Otra-Contrasena-Larga-2")

    def test_hay_que_saber_la_actual(self, api, ana):
        api.force_login(ana)

        respuesta = api.post(
            reverse("api-password"),
            {"actual": "la-que-no-es", "nueva": "Otra-Contrasena-Larga-2"},
            format="json",
        )

        assert respuesta.status_code == 400
        assert "actual" in respuesta.json()

    def test_la_nueva_pasa_los_validadores(self, api, ana):
        api.force_login(ana)

        respuesta = api.post(
            reverse("api-password"), {"actual": PASSWORD, "nueva": "1234"}, format="json"
        )

        assert respuesta.status_code == 400

    def test_sin_sesion_no_se_puede(self, api):
        respuesta = api.post(
            reverse("api-password"),
            {"actual": PASSWORD, "nueva": "Otra-Contrasena-Larga-2"},
            format="json",
        )

        assert respuesta.status_code in (401, 403)


class TestLosLimitesDeTasa:
    def test_el_get_y_el_post_no_van_al_mismo_cubo(self, rf):
        from apps.api.auth import SessionView

        vista = SessionView()

        vista.request = rf.get("/api/auth/session/")
        vista.get_throttles()
        ambito_get = vista.throttle_scope

        vista.request = rf.post("/api/auth/session/")
        vista.get_throttles()
        ambito_post = vista.throttle_scope

        assert ambito_post == "login"
        assert ambito_get != ambito_post

    def test_los_dos_ambitos_tienen_un_limite_configurado(self, settings):
        tarifas = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        assert "login" in tarifas
        assert "sesion" in tarifas
        assert int(tarifas["sesion"].split("/")[0]) > int(tarifas["login"].split("/")[0])

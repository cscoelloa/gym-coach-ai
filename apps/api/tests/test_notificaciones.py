import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.notifications.models import Notification, NotificationKind, Severity
from apps.notifications.services import unread_count

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-Api-1")


@pytest.fixture
def beto():
    return User.objects.create_user("beto", password="Contrasena-Larga-Api-1")


@pytest.fixture
def api(ana):
    cliente = APIClient()
    cliente.force_login(ana)
    return cliente


def crear(usuario, **extra):
    return Notification.objects.create(
        user=usuario,
        kind=extra.pop("kind", NotificationKind.PROGRESS_READY),
        title=extra.pop("title", "Aviso"),
        body=extra.pop("body", "Contenido"),
        **extra,
    )


class TestLaBandeja:
    def test_solo_se_ven_las_propias(self, api, ana, beto):
        crear(ana, title="Mía")
        crear(beto, title="Ajena")

        titulos = [n["title"] for n in api.get(reverse("api-notification-list")).json()["results"]]

        assert titulos == ["Mía"]

    def test_el_filtro_de_no_leidas_devuelve_el_total(self, api, ana):
        crear(ana)
        crear(ana)
        crear(ana, is_read=True)

        pagina = api.get(reverse("api-notification-list"), {"unread": "true"}).json()

        assert pagina["count"] == 2

    def test_trae_lo_que_la_pantalla_pinta(self, api, ana):
        crear(ana, severity=Severity.WARNING)

        aviso = api.get(reverse("api-notification-list")).json()["results"][0]

        assert aviso["kind_label"] == "Análisis de progreso listo"
        assert aviso["severity"] == "warning"
        assert "emailed_at" in aviso


class TestMarcarComoLeida:
    def test_marca_la_propia(self, api, ana):
        aviso = crear(ana)

        respuesta = api.patch(
            reverse("api-notification-detail", args=[aviso.pk]),
            {"is_read": True},
            format="json",
        )

        assert respuesta.status_code == 200
        aviso.refresh_from_db()
        assert aviso.is_read is True

    def test_la_de_otro_no_existe(self, api, beto):
        ajena = crear(beto)

        respuesta = api.patch(
            reverse("api-notification-detail", args=[ajena.pk]),
            {"is_read": True},
            format="json",
        )

        assert respuesta.status_code == 404
        ajena.refresh_from_db()
        assert ajena.is_read is False

    def test_no_se_puede_reescribir_el_contenido(self, api, ana):
        aviso = crear(ana, title="Estancamiento en press de banca")

        api.patch(
            reverse("api-notification-detail", args=[aviso.pk]),
            {"title": "Otra cosa", "body": "Otra cosa"},
            format="json",
        )

        aviso.refresh_from_db()
        assert aviso.title == "Estancamiento en press de banca"
        assert aviso.body == "Contenido"

    def test_marcar_todas_solo_afecta_a_las_propias(self, api, ana, beto):
        crear(ana)
        ajena = crear(beto)

        api.post(reverse("api-notification-read-all"))

        assert unread_count(ana) == 0
        ajena.refresh_from_db()
        assert ajena.is_read is False

    def test_marcar_todas_exige_post(self, api, ana):
        crear(ana)

        respuesta = api.get(reverse("api-notification-read-all"))

        assert respuesta.status_code == 405
        assert unread_count(ana) == 1


class TestSinSesion:
    def test_no_se_ve_la_bandeja(self):
        respuesta = APIClient().get(reverse("api-notification-list"))

        assert respuesta.status_code in (401, 403)

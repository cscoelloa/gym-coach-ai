from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.bodyweight.models import BodyWeightEntry

pytestmark = pytest.mark.django_db

User = get_user_model()
DIA = "2026-09-14"


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-Api-1")


@pytest.fixture
def api(ana):
    cliente = APIClient()
    cliente.force_login(ana)
    return cliente


class TestRegistrar:
    def test_guarda_el_peso(self, api, ana):
        respuesta = api.post(
            reverse("api-bodyweight-list"),
            {"date": DIA, "weight_kg": "70.5"},
            format="json",
        )

        assert respuesta.status_code == 201
        assert BodyWeightEntry.objects.filter(user=ana, weight_kg=Decimal("70.5")).exists()

    def test_el_dueño_sale_de_la_sesion_y_no_del_cuerpo(self, api, ana):
        otra = User.objects.create_user("beto", password="Contrasena-Larga-Api-1")

        api.post(
            reverse("api-bodyweight-list"),
            {"date": DIA, "weight_kg": "70.5", "user": otra.pk},
            format="json",
        )

        assert BodyWeightEntry.objects.get().user == ana

    def test_un_segundo_registro_del_mismo_dia_se_rechaza_con_explicacion(self, api):
        api.post(reverse("api-bodyweight-list"), {"date": DIA, "weight_kg": "70"}, format="json")

        respuesta = api.post(
            reverse("api-bodyweight-list"), {"date": DIA, "weight_kg": "71"}, format="json"
        )

        assert respuesta.status_code == 400
        assert "date" in respuesta.json()

    def test_pesarse_dos_veces_el_mismo_dia_actualiza(self, api, ana):
        primero = api.post(
            reverse("api-bodyweight-list"), {"date": DIA, "weight_kg": "70"}, format="json"
        ).json()

        api.patch(
            reverse("api-bodyweight-detail", args=[primero["id"]]),
            {"weight_kg": "71"},
            format="json",
        )

        registros = BodyWeightEntry.objects.filter(user=ana)
        assert registros.count() == 1
        assert registros.first().weight_kg == Decimal("71.00")

    def test_un_peso_imposible_se_rechaza(self, api):
        respuesta = api.post(
            reverse("api-bodyweight-list"), {"date": DIA, "weight_kg": "7"}, format="json"
        )

        assert respuesta.status_code == 400
        assert "weight_kg" in respuesta.json()


class TestBorrar:
    def test_borra_el_propio(self, api, ana):
        registro = BodyWeightEntry.objects.create(user=ana, date=DIA, weight_kg=Decimal("70"))

        respuesta = api.delete(reverse("api-bodyweight-detail", args=[registro.pk]))

        assert respuesta.status_code == 204
        assert not BodyWeightEntry.objects.filter(pk=registro.pk).exists()

    def test_el_de_otra_persona_no_existe(self, api):
        otra = User.objects.create_user("beto", password="Contrasena-Larga-Api-1")
        ajeno = BodyWeightEntry.objects.create(user=otra, date=DIA, weight_kg=Decimal("99"))

        respuesta = api.delete(reverse("api-bodyweight-detail", args=[ajeno.pk]))

        assert respuesta.status_code == 404
        assert BodyWeightEntry.objects.filter(pk=ajeno.pk).exists()

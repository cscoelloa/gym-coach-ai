from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.bodyweight.models import BodyWeightEntry

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-Api-1")


@pytest.fixture
def api(ana):
    cliente = APIClient()
    cliente.force_login(ana)
    return cliente


def registrar_pesos(usuario, cuantos):
    inicio = date(2026, 1, 1)
    BodyWeightEntry.objects.bulk_create(
        BodyWeightEntry(user=usuario, date=inicio + timedelta(days=dia), weight_kg=Decimal("70.0"))
        for dia in range(cuantos)
    )


class TestTotalDePaginas:
    def test_una_lista_dice_cuantas_paginas_tiene(self, api, ana):
        registrar_pesos(ana, 30)

        primera = api.get(reverse("api-bodyweight-list")).json()
        segunda = api.get(reverse("api-bodyweight-list"), {"page": 2}).json()

        assert primera["count"] == 30
        assert primera["total_pages"] == 2
        assert segunda["total_pages"] == 2
        assert len(segunda["results"]) == 5

    def test_una_lista_vacia_tiene_una_pagina(self, api):
        assert api.get(reverse("api-bodyweight-list")).json()["total_pages"] == 1

    def test_el_total_solo_cuenta_lo_propio(self, api):
        beto = User.objects.create_user("beto", password="Contrasena-Larga-Api-1")
        registrar_pesos(beto, 60)

        pagina = api.get(reverse("api-bodyweight-list")).json()

        assert pagina["count"] == 0
        assert pagina["total_pages"] == 1

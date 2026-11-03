import importlib
from datetime import date
from decimal import Decimal

import pytest
from django.apps import apps as registro
from django.contrib.auth import get_user_model

from apps.workouts.models import Exercise, MuscleGroup, SetLog, WorkoutSession

pytestmark = pytest.mark.django_db

User = get_user_model()

migracion = importlib.import_module("apps.workouts.migrations.0007_renumerar_series")


@pytest.fixture
def sesion():
    ana = User.objects.create_user("ana", password="Contrasena-Larga-1")
    return WorkoutSession.objects.create(user=ana, date=date(2026, 9, 14))


@pytest.fixture
def ejercicios():
    musculo = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    return [
        Exercise.objects.create(
            external_id=f"000{i}", name=nombre, slug=nombre.lower(),
            body_part="chest", equipment="barbell", target_muscle=musculo,
        )
        for i, nombre in enumerate(("Press", "Aperturas"), start=1)
    ]


def serie(sesion, ejercicio, numero, peso):
    return SetLog.objects.create(
        session=sesion, exercise=ejercicio, set_number=numero,
        weight_kg=Decimal(peso), reps=8,
    )


def numeros_y_pesos(sesion, ejercicio):
    return list(
        sesion.sets.filter(exercise=ejercicio)
        .order_by("set_number", "pk")
        .values_list("set_number", "weight_kg")
    )


class TestSiguienteNumero:
    def test_es_el_mayor_mas_uno_y_no_cuantas_hay_mas_uno(self, sesion, ejercicios):
        press = ejercicios[0]
        serie(sesion, press, 2, "60")
        serie(sesion, press, 3, "60")

        assert SetLog.siguiente_numero(sesion.pk, press.pk) == 4

    def test_la_primera_es_la_1(self, sesion, ejercicios):
        assert SetLog.siguiente_numero(sesion.pk, ejercicios[0].pk) == 1


class TestRenumerar:
    def test_cierra_huecos_conservando_el_orden(self, sesion, ejercicios):
        press = ejercicios[0]
        serie(sesion, press, 2, "60")
        serie(sesion, press, 5, "70")

        SetLog.renumerar(sesion.pk, press.pk)

        assert numeros_y_pesos(sesion, press) == [(1, Decimal("60")), (2, Decimal("70"))]


class TestLaMigracion:
    def test_deshace_los_repetidos_en_el_orden_en_que_se_guardaron(self, sesion, ejercicios):
        press, aperturas = ejercicios
        serie(sesion, press, 2, "60")
        serie(sesion, press, 3, "65")
        serie(sesion, press, 3, "70")
        serie(sesion, aperturas, 1, "20")
        serie(sesion, aperturas, 2, "20")

        migracion.renumerar(registro, None)

        assert numeros_y_pesos(sesion, press) == [
            (1, Decimal("60")), (2, Decimal("65")), (3, Decimal("70")),
        ]
        assert [n for n, _ in numeros_y_pesos(sesion, aperturas)] == [1, 2]

    def test_cada_sesion_cuenta_por_su_cuenta(self, sesion, ejercicios):
        press = ejercicios[0]
        otra = WorkoutSession.objects.create(user=sesion.user, date=date(2026, 9, 16))
        serie(sesion, press, 4, "60")
        serie(otra, press, 7, "60")

        migracion.renumerar(registro, None)

        assert sesion.sets.get().set_number == 1
        assert otra.sets.get().set_number == 1

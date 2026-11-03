from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.metrics.catalog.strength import personal_records
from apps.metrics.catalog.volume import effective_sets_by_muscle, weekly_tonnage
from apps.metrics.context import MetricContext
from apps.metrics.loads import effective_load, total_work
from apps.workouts.models import Exercise, MuscleGroup, SetLog, WorkoutSession

pytestmark = pytest.mark.django_db

User = get_user_model()

HOY = date(2026, 9, 14)


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-1")


@pytest.fixture
def espalda():
    return MuscleGroup.objects.create(slug="lats", name="Dorsales")


@pytest.fixture
def remo_una_mano(espalda):
    return Exercise.objects.create(
        external_id="0001", name="one arm dumbbell row", slug="remo-una-mano",
        body_part="back", equipment="dumbbell", target_muscle=espalda,
        is_global=True, is_unilateral=True,
    )


@pytest.fixture
def remo_barra(espalda):
    return Exercise.objects.create(
        external_id="0002", name="barbell row", slug="remo-barra",
        body_part="back", equipment="barbell", target_muscle=espalda,
        is_global=True, is_unilateral=False,
    )


def registra(user, exercise, *, peso, reps, series=1, dia=None):
    sesion = WorkoutSession.objects.create(user=user, date=dia or HOY)
    for numero in range(1, series + 1):
        SetLog.objects.create(
            session=sesion, exercise=exercise, set_number=numero,
            weight_kg=Decimal(str(peso)), reps=reps,
        )
    return sesion


class TestLasDosFunciones:
    def test_effective_load_es_lo_que_se_levanta_en_la_serie(self, ana, remo_una_mano):
        registra(ana, remo_una_mano, peso=30, reps=10)
        serie = SetLog.objects.get()

        assert effective_load(serie, None) == Decimal("30")

    def test_total_work_cuenta_los_dos_lados(self, ana, remo_una_mano):
        registra(ana, remo_una_mano, peso=30, reps=10)
        serie = SetLog.objects.get()

        assert total_work(serie, None) == Decimal("60")

    def test_en_un_bilateral_las_dos_coinciden(self, ana, remo_barra):
        registra(ana, remo_barra, peso=30, reps=10)
        serie = SetLog.objects.get()

        assert effective_load(serie, None) == total_work(serie, None) == Decimal("30")


class TestLaTrampa:
    def test_el_tonelaje_SI_se_dobla(self, ana, remo_una_mano):
        registra(ana, remo_una_mano, peso=30, reps=10, series=3)

        resultado = weekly_tonnage(MetricContext(user=ana))

        assert resultado.value == 1800

    def test_el_record_personal_NO_se_dobla(self, ana, remo_una_mano):
        registra(ana, remo_una_mano, peso=30, reps=1)

        resultado = personal_records(MetricContext(user=ana))

        pesos = [fila[1] for fila in resultado.rows]
        assert 30 in pesos or "30" in {str(p) for p in pesos}, resultado.rows
        assert 60 not in pesos, "el 1RM se ha doblado: el ×2 está en effective_load"

    def test_las_series_efectivas_NO_cambian(self, ana, remo_una_mano, remo_barra):
        registra(ana, remo_una_mano, peso=30, reps=10, series=3)
        uni = effective_sets_by_muscle(MetricContext(user=ana)).value

        SetLog.objects.all().delete()
        WorkoutSession.objects.all().delete()
        registra(ana, remo_barra, peso=30, reps=10, series=3)
        bi = effective_sets_by_muscle(MetricContext(user=ana)).value

        assert uni == bi


class TestElMarcadoDelCatalogo:
    def test_marca_los_inequivocos(self, remo_una_mano):
        assert remo_una_mano.is_unilateral is True

    def test_deja_sin_marcar_los_ambiguos(self, espalda):
        ambiguo = Exercise.objects.create(
            external_id="0003", name="alternate heel touchers", slug="heel",
            body_part="waist", equipment="body weight", target_muscle=espalda,
            is_global=True,
        )

        assert ambiguo.is_unilateral is False

    def test_por_defecto_no_es_unilateral(self, remo_barra):
        assert remo_barra.is_unilateral is False

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.workouts.history import best_set, last_performance, progression_hint
from apps.workouts.models import Exercise, MuscleGroup, SetLog, WorkoutSession

pytestmark = pytest.mark.django_db

User = get_user_model()

HOY = date(2026, 9, 14)


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-1")


@pytest.fixture
def musculo():
    return MuscleGroup.objects.create(slug="pectorals", name="Pectorales")


@pytest.fixture
def press(musculo):
    return Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press-banca",
        body_part="chest", equipment="barbell", target_muscle=musculo,
    )


@pytest.fixture
def dominada(musculo):
    return Exercise.objects.create(
        external_id="0002", name="Dominada", slug="dominada",
        body_part="back", equipment="body weight", target_muscle=musculo,
        is_bodyweight=True,
    )


def registra(user, exercise, dia, series, **extra):
    sesion = WorkoutSession.objects.create(user=user, date=dia)
    for numero, (peso, reps) in enumerate(series, start=1):
        SetLog.objects.create(
            session=sesion, exercise=exercise, set_number=numero,
            weight_kg=None if peso is None else Decimal(str(peso)), reps=reps, **extra,
        )
    return sesion


class TestUltimaVez:
    def test_devuelve_las_series_de_la_sesion_mas_reciente(self, ana, press):
        registra(ana, press, HOY - timedelta(days=10), [(80, 8), (80, 8)])
        registra(ana, press, HOY - timedelta(days=3), [(85, 8), (85, 7)])

        anterior = last_performance(ana, press)

        assert anterior.date == HOY - timedelta(days=3)
        assert anterior.summary == "85×8, 85×7"

    def test_excluye_la_sesion_en_curso(self, ana, press):
        registra(ana, press, HOY - timedelta(days=3), [(85, 8)])
        actual = registra(ana, press, HOY, [(90, 5)])

        anterior = last_performance(ana, press, before_session=actual)

        assert anterior.date == HOY - timedelta(days=3)
        assert anterior.summary == "85×8"

    def test_sin_historial_devuelve_None(self, ana, press):
        assert last_performance(ana, press) is None

    def test_ignora_los_calentamientos(self, ana, press):
        registra(ana, press, HOY - timedelta(days=3), [(40, 10)], is_warmup=True)

        assert last_performance(ana, press) is None

    def test_no_mezcla_el_historial_de_otra_persona(self, ana, press):
        beto = User.objects.create_user("beto", password="Contrasena-Larga-2")
        registra(beto, press, HOY - timedelta(days=3), [(200, 8)])

        assert last_performance(ana, press) is None

    def test_el_resumen_no_arrastra_decimales_inutiles(self, ana, press):
        registra(ana, press, HOY - timedelta(days=3), [(85.0, 8), (87.5, 6)])

        assert last_performance(ana, press).summary == "85×8, 87.5×6"


class TestMejorSerie:
    def test_el_peso_mas_alto(self, ana, press):
        registra(ana, press, HOY - timedelta(days=10), [(80, 8)])
        registra(ana, press, HOY - timedelta(days=3), [(92.5, 3), (85, 8)])

        assert best_set(ana, press) == Decimal("92.5")

    def test_sin_pesos_registrados_devuelve_None(self, ana, press):
        registra(ana, press, HOY, [(None, 8)])

        assert best_set(ana, press) is None


class TestReglaDeProgresion:
    def test_sugiere_cuando_se_completo_el_rango_entero(self, ana, press):
        registra(ana, press, HOY - timedelta(days=3), [(85, 8), (85, 8), (85, 8)])

        sugerencia = progression_hint(ana, press, target_reps_max=8)

        assert sugerencia is not None
        assert "87.5 kg" in sugerencia

    def test_NO_sugiere_si_una_sola_serie_se_quedo_corta(self, ana, press):
        registra(ana, press, HOY - timedelta(days=3), [(85, 8), (85, 8), (85, 6)])

        assert progression_hint(ana, press, target_reps_max=8) is None

    def test_NO_sugiere_sin_historial(self, ana, press):
        assert progression_hint(ana, press, target_reps_max=8) is None

    def test_NO_sugiere_sin_objetivo_de_repeticiones(self, ana, press):
        registra(ana, press, HOY - timedelta(days=3), [(85, 8)])

        assert progression_hint(ana, press, target_reps_max=None) is None

    def test_en_peso_corporal_sugiere_repeticiones_y_no_kilos(self, ana, dominada):
        registra(ana, dominada, HOY - timedelta(days=3), [(None, 10), (None, 10)])

        sugerencia = progression_hint(ana, dominada, target_reps_max=10)

        assert sugerencia is not None
        assert "kg" not in sugerencia
        assert "añadir una más" in sugerencia

    def test_el_salto_depende_del_equipamiento(self, ana, musculo):
        polea = Exercise.objects.create(
            external_id="0003", name="Jalón", slug="jalon", body_part="back",
            equipment="cable", target_muscle=musculo,
        )
        registra(ana, polea, HOY - timedelta(days=3), [(50, 12), (50, 12)])

        assert "55 kg" in progression_hint(ana, polea, target_reps_max=12)

    def test_parte_del_peso_mas_alto_de_la_ultima_vez(self, ana, press):
        registra(ana, press, HOY - timedelta(days=3), [(85, 8), (80, 8)])

        assert "87.5 kg" in progression_hint(ana, press, target_reps_max=8)

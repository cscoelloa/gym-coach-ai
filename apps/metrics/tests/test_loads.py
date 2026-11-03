from decimal import Decimal

import pytest

from apps.metrics.loads import (
    DIRECT_CONTRIBUTION,
    INDIRECT_CONTRIBUTION,
    effective_load,
    is_effective_set,
    is_working_set,
    muscle_contributions,
)

pytestmark = pytest.mark.django_db


class TestCargaEfectiva:
    def test_ejercicio_con_peso_usa_el_peso_registrado(self, bench, log_set):
        set_log = log_set(bench, weight=100)

        assert effective_load(set_log, Decimal("75")) == Decimal("100")

    def test_peso_corporal_usa_el_peso_de_la_persona(self, pullup, log_set):
        set_log = log_set(pullup, weight=None, reps=10)

        assert effective_load(set_log, Decimal("75")) == Decimal("75")

    def test_peso_corporal_con_lastre_suma(self, pullup, log_set):
        set_log = log_set(pullup, weight=10)

        assert effective_load(set_log, Decimal("75")) == Decimal("85")

    def test_sin_peso_registrado_devuelve_none_en_vez_de_cero(self, pullup, log_set):
        set_log = log_set(pullup, weight=None)

        assert effective_load(set_log, None) is None


class TestSeriesQueCuentan:
    def test_una_serie_normal_cuenta(self, bench, log_set):
        assert is_working_set(log_set(bench)) is True

    def test_el_calentamiento_no_cuenta(self, bench, log_set):
        assert is_working_set(log_set(bench, warmup=True)) is False

    def test_una_serie_no_completada_no_cuenta(self, bench, log_set):
        assert is_working_set(log_set(bench, completed=False)) is False

    def test_el_cardio_no_cuenta(self, treadmill, log_set):
        assert is_working_set(log_set(treadmill)) is False


class TestSeriesEfectivas:
    def test_sin_rpe_cuenta_igual(self, bench, log_set):
        assert is_effective_set(log_set(bench, rpe=None)) is True

    def test_rpe_alto_cuenta(self, bench, log_set):
        assert is_effective_set(log_set(bench, rpe=9)) is True

    def test_rpe_en_el_umbral_cuenta(self, bench, log_set):
        assert is_effective_set(log_set(bench, rpe=7)) is True

    def test_rpe_bajo_se_descarta(self, bench, log_set):
        assert is_effective_set(log_set(bench, rpe=5)) is False

    def test_un_calentamiento_nunca_es_efectivo(self, bench, log_set):
        assert is_effective_set(log_set(bench, rpe=9, warmup=True)) is False


class TestContribucionMuscular:
    def test_el_objetivo_cuenta_entero_y_los_secundarios_la_mitad(self, bench):
        contribuciones = muscle_contributions(bench)

        assert contribuciones["pectorals"] == DIRECT_CONTRIBUTION
        assert contribuciones["triceps"] == INDIRECT_CONTRIBUTION
        assert contribuciones["delts"] == INDIRECT_CONTRIBUTION

    def test_un_musculo_repetido_no_se_cuenta_dos_veces(self, make_exercise):
        exercise = make_exercise("Raro", target="lats", secondary=("lats", "triceps"))

        contribuciones = muscle_contributions(exercise)

        assert contribuciones["lats"] == DIRECT_CONTRIBUTION
        assert len(contribuciones) == 2

    def test_sin_musculo_objetivo_no_revienta(self, make_exercise):
        exercise = make_exercise("Sin objetivo", target=None, secondary=("triceps",))

        assert muscle_contributions(exercise) == {"triceps": INDIRECT_CONTRIBUTION}

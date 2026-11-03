import pytest

from apps.metrics.catalog.strength import (
    STALL_THRESHOLD_WEEKS,
    e1rm_progression,
    personal_records,
    progression_slope,
    stalled_exercises,
)
from apps.metrics.context import MetricContext

pytestmark = pytest.mark.django_db

DAYS_PER_WEEK = 7


def rows_by_exercise(result):
    return {row[0]: row for row in result.rows}


class TestRecordsPersonales:
    def test_guarda_el_mejor_peso_y_las_mejores_reps(self, user, bench, log_set):
        log_set(bench, weight=100, reps=5)
        log_set(bench, weight=90, reps=12)

        fila = rows_by_exercise(personal_records(MetricContext(user=user)))["Press de banca"]

        assert fila[1] == 100.0
        assert fila[2] == 12

    def test_una_serie_de_muchas_reps_no_genera_record_de_1rm(self, user, bench, log_set):
        log_set(bench, weight=100, reps=20)

        fila = rows_by_exercise(personal_records(MetricContext(user=user)))["Press de banca"]

        assert fila[3] == "—"

    def test_el_peso_corporal_cuenta_como_record(self, user, pullup, log_set, log_weight):
        log_weight(75)
        log_set(pullup, weight=None, reps=8)

        fila = rows_by_exercise(personal_records(MetricContext(user=user)))["Dominada"]

        assert fila[1] == 75.0


class TestProgresion:
    def test_mide_el_cambio_entre_la_primera_y_la_ultima_semana(self, user, bench, log_set):
        log_set(bench, weight=100, reps=5, days_ago=3 * DAYS_PER_WEEK)
        log_set(bench, weight=110, reps=5, days_ago=0)

        fila = rows_by_exercise(e1rm_progression(MetricContext(user=user)))["Press de banca"]

        assert fila[3] == pytest.approx(11.7, abs=0.05)

    def test_una_sola_semana_no_da_progresion(self, user, bench, log_set):
        log_set(bench, weight=100, reps=5)

        resultado = e1rm_progression(MetricContext(user=user))

        assert resultado.rows == []
        assert resultado.notes

    def test_la_pendiente_necesita_varias_semanas(self, user, bench, log_set):
        for week in range(4):
            log_set(bench, weight=100 + week * 5, reps=5, days_ago=(3 - week) * DAYS_PER_WEEK)

        fila = rows_by_exercise(progression_slope(MetricContext(user=user)))["Press de banca"]

        assert fila[1] > 0
        assert fila[2] == 4


class TestEstancamiento:
    def test_detecta_un_ejercicio_sin_records_recientes(self, user, bench, log_set):
        log_set(bench, weight=120, reps=5, days_ago=6 * DAYS_PER_WEEK)
        for week in range(5, -1, -1):
            log_set(bench, weight=100, reps=5, days_ago=week * DAYS_PER_WEEK)

        fila = rows_by_exercise(stalled_exercises(MetricContext(user=user)))["Press de banca"]

        assert fila[1] >= STALL_THRESHOLD_WEEKS

    def test_quien_progresa_no_sale_estancado(self, user, bench, log_set):
        for week in range(6):
            log_set(bench, weight=100 + week * 2.5, reps=5, days_ago=(5 - week) * DAYS_PER_WEEK)

        resultado = stalled_exercises(MetricContext(user=user))

        assert resultado.rows == []
        assert resultado.value == 0

    def test_sin_datos_no_inventa_estancamientos(self, user):
        resultado = stalled_exercises(MetricContext(user=user))

        assert resultado.value == 0
        assert resultado.coverage == 0.0

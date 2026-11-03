from datetime import date

import pytest

from apps.metrics.catalog.volume import (
    effective_sets_by_muscle,
    training_frequency_by_muscle,
    weekly_tonnage,
    weekly_volume_by_muscle,
)
from apps.metrics.context import MetricContext

pytestmark = pytest.mark.django_db


def series_as_dict(result):
    return {point["label"]: point["value"] for point in result.series}


class TestVolumenPorMusculo:
    def test_el_objetivo_suma_uno_y_los_secundarios_medio(self, user, bench, log_set):
        log_set(bench)

        volumen = series_as_dict(weekly_volume_by_muscle(MetricContext(user=user)))

        assert volumen["Pectorales"] == 1.0
        assert volumen["Tríceps"] == 0.5
        assert volumen["Deltoides"] == 0.5

    def test_varias_series_se_acumulan(self, user, bench, log_set):
        for _ in range(4):
            log_set(bench)

        volumen = series_as_dict(weekly_volume_by_muscle(MetricContext(user=user)))

        assert volumen["Pectorales"] == 4.0
        assert volumen["Tríceps"] == 2.0

    def test_los_calentamientos_no_suman(self, user, bench, log_set):
        log_set(bench)
        log_set(bench, warmup=True)

        volumen = series_as_dict(weekly_volume_by_muscle(MetricContext(user=user)))

        assert volumen["Pectorales"] == 1.0

    def test_las_series_no_completadas_no_suman(self, user, bench, log_set):
        log_set(bench)
        log_set(bench, completed=False)

        volumen = series_as_dict(weekly_volume_by_muscle(MetricContext(user=user)))

        assert volumen["Pectorales"] == 1.0

    def test_el_cardio_queda_fuera(self, user, treadmill, log_set):
        log_set(treadmill)

        resultado = weekly_volume_by_muscle(MetricContext(user=user))

        assert resultado.series == []
        assert resultado.coverage == 0.0

    def test_sin_datos_avisa_en_vez_de_mostrar_cero(self, user):
        resultado = weekly_volume_by_muscle(MetricContext(user=user))

        assert resultado.value is None
        assert resultado.coverage == 0.0
        assert resultado.notes


class TestSeriesEfectivas:
    def test_sin_rpe_cuenta_todo_y_el_numero_es_de_fiar(self, user, bench, log_set):
        log_set(bench, rpe=None)
        log_set(bench, rpe=None)

        resultado = effective_sets_by_muscle(MetricContext(user=user))

        assert series_as_dict(resultado)["Pectorales"] == 2.0
        assert resultado.coverage == 1.0

    def test_con_rpe_descarta_las_flojas(self, user, bench, log_set):
        log_set(bench, rpe=9)
        log_set(bench, rpe=4)

        resultado = effective_sets_by_muscle(MetricContext(user=user))

        assert series_as_dict(resultado)["Pectorales"] == 1.0
        assert resultado.coverage == 1.0

    def test_un_rpe_que_llegue_por_la_api_sigue_descartando(self, user, bench, log_set):
        log_set(bench, rpe=4)
        log_set(bench, rpe=None)
        log_set(bench, rpe=None)
        log_set(bench, rpe=None)

        resultado = effective_sets_by_muscle(MetricContext(user=user))

        assert series_as_dict(resultado)["Pectorales"] == 3.0
        assert resultado.coverage == 1.0


class TestFrecuencia:
    def test_cuenta_dias_distintos_no_series(self, user, bench, log_set):
        martes, jueves = date(2026, 9, 8), date(2026, 9, 10)
        log_set(bench, on_date=martes)
        log_set(bench, on_date=martes)
        log_set(bench, on_date=jueves)

        frecuencia = series_as_dict(training_frequency_by_muscle(MetricContext(user=user)))

        assert frecuencia["Pectorales"] == 2.0

    def test_varias_series_el_mismo_dia_son_frecuencia_uno(self, user, bench, log_set):
        for _ in range(5):
            log_set(bench, days_ago=0)

        frecuencia = series_as_dict(training_frequency_by_muscle(MetricContext(user=user)))

        assert frecuencia["Pectorales"] == 1.0


class TestTonelaje:
    def test_suma_peso_por_repeticiones(self, user, bench, log_set):
        log_set(bench, weight=100, reps=10)

        resultado = weekly_tonnage(MetricContext(user=user))

        assert resultado.value == 1000
        assert resultado.coverage == 1.0

    def test_el_peso_corporal_cuenta_si_hay_registro(self, user, pullup, log_set, log_weight):
        log_weight(75)
        log_set(pullup, weight=None, reps=10)

        resultado = weekly_tonnage(MetricContext(user=user))

        assert resultado.value == 750

    def test_el_lastre_se_suma_al_peso_corporal(self, user, pullup, log_set, log_weight):
        log_weight(75)
        log_set(pullup, weight=10, reps=10)

        assert weekly_tonnage(MetricContext(user=user)).value == 850

    def test_sin_peso_registrado_no_cuenta_y_avisa(self, user, pullup, log_set):
        log_set(pullup, weight=None, reps=10)

        resultado = weekly_tonnage(MetricContext(user=user))

        assert resultado.value is None
        assert resultado.coverage == 0.0
        assert any("peso corporal" in nota for nota in resultado.notes)

    def test_usa_un_peso_anterior_a_la_ventana(self, user, pullup, log_set, log_weight):
        log_weight(80, days_ago=200)
        log_set(pullup, weight=None, reps=10)

        assert weekly_tonnage(MetricContext(user=user)).value == 800

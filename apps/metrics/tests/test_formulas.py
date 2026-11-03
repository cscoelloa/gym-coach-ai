import pytest

from apps.metrics.formulas import (
    MAX_REPS_FOR_E1RM,
    coverage_of,
    epley_1rm,
    linear_slope,
    moving_average,
    week_key,
)


class TestEpley:
    def test_una_repeticion_es_el_propio_peso(self):
        assert epley_1rm(100, 1) == 100

    def test_mas_repeticiones_estiman_mas_1rm(self):
        assert epley_1rm(100, 5) == pytest.approx(116.67, abs=0.01)

    @pytest.mark.parametrize("reps", [MAX_REPS_FOR_E1RM + 1, 20, 100])
    def test_ignora_series_de_muchas_repeticiones(self, reps):
        assert epley_1rm(100, reps) is None

    @pytest.mark.parametrize(
        "weight, reps",
        [(None, 5), (100, None), (0, 5), (-10, 5), (100, 0)],
    )
    def test_devuelve_none_en_vez_de_inventar(self, weight, reps):
        assert epley_1rm(weight, reps) is None


class TestPendiente:
    def test_pendiente_positiva(self):
        assert linear_slope([(0, 100), (1, 102), (2, 104)]) == pytest.approx(2.0)

    def test_pendiente_negativa(self):
        assert linear_slope([(0, 100), (1, 98)]) == pytest.approx(-2.0)

    def test_sin_progresion_es_cero(self):
        assert linear_slope([(0, 100), (1, 100), (2, 100)]) == pytest.approx(0.0)

    @pytest.mark.parametrize("points", [[], [(0, 100)]])
    def test_hacen_falta_al_menos_dos_puntos(self, points):
        assert linear_slope(points) is None

    def test_todas_las_x_iguales_no_tiene_pendiente(self):
        assert linear_slope([(1, 100), (1, 110)]) is None


class TestMediaMovil:
    def test_suaviza(self):
        assert moving_average([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]

    def test_las_posiciones_sin_ventana_completa_salen_none(self):
        resultado = moving_average([70, 71, 72], 3)
        assert resultado[:2] == [None, None]
        assert resultado[2] == pytest.approx(71)

    def test_ventana_invalida(self):
        with pytest.raises(ValueError):
            moving_average([1, 2], 0)


class TestCobertura:
    def test_todo_disponible(self):
        assert coverage_of(10, 10) == 1.0

    def test_parcial(self):
        assert coverage_of(2, 10) == 0.2

    def test_sin_datos_la_cobertura_es_cero_no_uno(self):
        assert coverage_of(0, 0) == 0.0


def test_clave_de_semana_es_ordenable():
    from datetime import date

    claves = [week_key(date(2026, 1, 5)), week_key(date(2026, 9, 14))]
    assert claves == sorted(claves)
    assert claves[1] == "2026-W38"

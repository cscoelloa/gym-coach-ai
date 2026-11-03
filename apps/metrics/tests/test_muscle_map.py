from datetime import date, timedelta

import pytest

from apps.metrics.summary import EFFECTIVE_SETS_LEVELS, _muscle_level, muscle_map
from apps.workouts.taxonomy import MUSCLE_ES, MUSCLE_WITHOUT_REGION, muscle_slug

LUNES = date(2026, 9, 14)


class TestLosTonos:
    @pytest.mark.parametrize(
        "series,esperado",
        [
            (0, 0),
            (0.5, 1),
            (4.9, 1),
            (5, 2),
            (9.9, 2),
            (10, 3),
            (14.9, 3),
            (15, 4),
            (40, 4),
        ],
    )
    def test_los_cortes_son_los_declarados(self, series, esperado):
        assert _muscle_level(series) == esperado

    def test_cero_tiene_su_propio_tono(self):
        assert _muscle_level(0) == 0
        assert _muscle_level(0.5) == 1

    def test_hay_un_tono_por_corte_mas_el_cero(self):
        assert _muscle_level(max(EFFECTIVE_SETS_LEVELS) + 1) == len(EFFECTIVE_SETS_LEVELS) + 1


@pytest.mark.django_db
class TestElReparto:
    def test_usa_el_mismo_reparto_que_el_resto_de_metricas(self, user, bench, log_set):
        for _ in range(4):
            log_set(bench, on_date=LUNES)

        mapa = muscle_map(user, on_date=LUNES)

        assert mapa["sets"]["pectorals"] == 4.0
        assert mapa["sets"]["triceps"] == 2.0
        assert mapa["sets"]["delts"] == 2.0

    def test_el_calentamiento_no_cuenta(self, user, bench, log_set):
        log_set(bench, on_date=LUNES)
        log_set(bench, on_date=LUNES, warmup=True)

        assert muscle_map(user, on_date=LUNES)["sets"]["pectorals"] == 1.0

    def test_una_serie_por_debajo_del_umbral_de_rpe_no_cuenta(self, user, bench, log_set):
        log_set(bench, on_date=LUNES, rpe=5)

        assert muscle_map(user, on_date=LUNES)["sets"] == {}

    def test_solo_mira_la_semana_pedida(self, user, bench, log_set):
        log_set(bench, on_date=LUNES)
        log_set(bench, on_date=LUNES - timedelta(days=7))

        assert muscle_map(user, on_date=LUNES)["sets"]["pectorals"] == 1.0
        assert muscle_map(user, weeks=2, on_date=LUNES)["sets"]["pectorals"] == 2.0

    def test_no_se_ve_lo_de_otra_persona(self, user, bench, log_set, django_user_model):
        log_set(bench, on_date=LUNES)
        otra = django_user_model.objects.create_user("otra", password="Contrasena-Larga-2")

        assert muscle_map(otra, on_date=LUNES)["sets"] == {}


@pytest.mark.django_db
class TestLaFormaDeLaRespuesta:
    def test_estan_todos_los_musculos_aunque_esten_a_cero(self, user):
        niveles = muscle_map(user, on_date=LUNES)["levels"]

        esperados = {muscle_slug(nombre) for nombre in MUSCLE_ES}
        assert set(niveles) == esperados
        assert all(v == 0 for v in niveles.values())
        assert not any(v is None for v in niveles.values())

    def test_las_claves_son_slugs_y_no_nombres_canonicos(self, user):
        niveles = muscle_map(user, on_date=LUNES)["levels"]

        assert "upper-back" in niveles
        assert "upper back" not in niveles
        assert not any(" " in clave for clave in niveles)

    def test_el_total_suma_lo_mismo_que_el_detalle(self, user, bench, log_set):
        for _ in range(3):
            log_set(bench, on_date=LUNES)

        mapa = muscle_map(user, on_date=LUNES)

        assert mapa["total_sets"] == pytest.approx(sum(mapa["sets"].values()))

    def test_un_musculo_sin_region_sigue_teniendo_nivel(self, user, treadmill, log_set):
        assert MUSCLE_WITHOUT_REGION

        niveles = muscle_map(user, on_date=LUNES)["levels"]
        for slug in MUSCLE_WITHOUT_REGION:
            assert slug in niveles

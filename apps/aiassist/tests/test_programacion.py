import pytest

from apps.aiassist.models import PROGRAMACION_POR_DEFECTO, ProgrammingRules, TrainingGoal
from apps.aiassist.schemas import PlannedExercise, PlannedRoutine, RoutinePlan, ScheduledDay
from apps.aiassist.services import programacion
from apps.aiassist.services.split import DiaDelReparto
from apps.workouts.models import Exercise, MuscleGroup

pytestmark = pytest.mark.django_db


@pytest.fixture
def musculos():
    return {
        slug: MuscleGroup.objects.create(slug=slug, name=nombre)
        for slug, nombre in [
            ("pectorals", "Pectorales"), ("triceps", "Tríceps"), ("delts", "Deltoides")
        ]
    }


@pytest.fixture
def catalogo(musculos):
    press = Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press", body_part="chest",
        equipment="barbell", target_muscle=musculos["pectorals"], is_global=True,
    )
    press.secondary_muscles.add(musculos["triceps"], musculos["delts"])

    extension = Exercise.objects.create(
        external_id="0002", name="Extensión de tríceps", slug="extension", body_part="upper arms",
        equipment="cable", target_muscle=musculos["triceps"], is_global=True,
    )
    elevacion = Exercise.objects.create(
        external_id="0003", name="Elevación lateral", slug="elevacion", body_part="shoulders",
        equipment="dumbbell", target_muscle=musculos["delts"], is_global=True,
    )
    return {e.external_id: e for e in (press, extension, elevacion)}


def plan(ejercicios: list[tuple[str, int, int, int, int]]) -> RoutinePlan:
    rutina = PlannedRoutine(
        name="Empuje",
        exercises=[
            PlannedExercise(
                external_id=ext, sets=series, reps_min=minimo, reps_max=maximo,
                rest_seconds=descanso,
            )
            for ext, series, minimo, maximo, descanso in ejercicios
        ],
    )
    return RoutinePlan(
        name="Programa", description="Para probar", routines=[rutina],
        schedule=[
            ScheduledDay(weekday=dia, routine_name="Empuje" if dia == 0 else "")
            for dia in range(7)
        ],
        rationale="Porque sí",
    )


def dia(musculos: list[str], ejercicios: int = 6) -> DiaDelReparto:
    return DiaDelReparto(0, tuple(musculos), None, ejercicios)


@pytest.fixture
def hipertrofia():
    return programacion.reglas_de(TrainingGoal.HYPERTROPHY)


class TestDeDondeSalenLasReglas:
    def test_las_filas_las_crea_la_migracion(self):
        assert ProgrammingRules.objects.count() == len(TrainingGoal.values)

    def test_las_de_la_base_mandan_sobre_las_del_codigo(self):
        ProgrammingRules.objects.filter(goal=TrainingGoal.HYPERTROPHY).update(sets_min=5)

        assert programacion.reglas_de(TrainingGoal.HYPERTROPHY).sets_min == 5

    def test_sin_fila_se_usan_las_del_codigo(self):
        ProgrammingRules.objects.filter(goal=TrainingGoal.HYPERTROPHY).delete()

        reglas = programacion.reglas_de(TrainingGoal.HYPERTROPHY)

        assert reglas.sets_min == PROGRAMACION_POR_DEFECTO[TrainingGoal.HYPERTROPHY]["sets_min"]

    def test_un_objetivo_desconocido_cae_en_hipertrofia(self):
        assert programacion.reglas_de("lo-que-sea").goal == TrainingGoal.HYPERTROPHY


class TestCompuestoOAislamiento:
    def test_el_que_mueve_varios_musculos_es_compuesto(self, catalogo):
        assert programacion.es_compuesto(catalogo["0001"])

    def test_el_que_mueve_uno_no(self, catalogo):
        assert not programacion.es_compuesto(catalogo["0002"])


class TestSeriesRepeticionesYDescanso:
    def test_un_plan_que_cumple_no_tiene_problemas(self, catalogo, hipertrofia):
        correcto = plan([("0001", 4, 8, 12, 150), ("0002", 3, 12, 15, 90)])

        assert programacion.problemas(correcto, catalogo, hipertrofia) == []

    def test_una_serie_suelta_no_es_hipertrofia(self, catalogo, hipertrofia):
        flojo = plan([("0001", 1, 8, 12, 150)])

        fallos = programacion.problemas(flojo, catalogo, hipertrofia)

        assert any("lleva 1 series" in f and "van de 3 a 4" in f for f in fallos)

    def test_sesenta_segundos_en_un_compuesto_no_llegan(self, catalogo, hipertrofia):
        corto = plan([("0001", 4, 8, 12, 60)])

        fallos = programacion.problemas(corto, catalogo, hipertrofia)

        assert any("descansa 60 s" in f and "120" in f for f in fallos)

    def test_el_aislamiento_aguanta_con_menos_descanso(self, catalogo, hipertrofia):
        aislamiento = plan([("0003", 3, 12, 15, 90)])

        assert programacion.problemas(aislamiento, catalogo, hipertrofia) == []

    def test_las_repeticiones_son_una_banda_no_un_numero(self, catalogo, hipertrofia):
        variado = plan([("0001", 4, 8, 12, 150), ("0003", 3, 12, 20, 90)])

        assert programacion.problemas(variado, catalogo, hipertrofia) == []

    def test_tres_repeticiones_se_salen_de_la_banda_de_hipertrofia(self, catalogo, hipertrofia):
        fuerza = plan([("0001", 4, 3, 5, 180)])

        fallos = programacion.problemas(fuerza, catalogo, hipertrofia)

        assert any("fuera del rango 6-20" in f for f in fallos)

    def test_cada_objetivo_tiene_lo_suyo(self, catalogo):
        pesado = plan([("0001", 5, 3, 5, 180)])

        assert programacion.problemas(
            pesado, catalogo, programacion.reglas_de(TrainingGoal.STRENGTH)
        ) == []


class TestVolumenPorMusculo:
    def test_un_musculo_nombrado_y_sin_series_se_detecta(self, catalogo, hipertrofia):
        solo_pecho = plan([("0001", 4, 8, 12, 150), ("0001", 4, 8, 12, 150)])
        reparto = [dia(["pectorals", "triceps"], ejercicios=4)]

        fallos = programacion.problemas(
            solo_pecho, catalogo, hipertrofia, dias=[(reparto[0], solo_pecho.routines[0])]
        )

        assert any("Tríceps (0)" in f for f in fallos)

    def test_con_volumen_repartido_no_se_queja(self, catalogo, hipertrofia):
        repartido = plan([
            ("0001", 3, 8, 12, 150), ("0001", 3, 8, 12, 150),
            ("0002", 3, 12, 15, 90), ("0002", 3, 12, 15, 90),
        ])
        reparto = dia(["pectorals", "triceps"], ejercicios=4)

        fallos = programacion.problemas(
            repartido, catalogo, hipertrofia, dias=[(reparto, repartido.routines[0])]
        )

        assert fallos == []


class TestElMinimoSeAcotaALoPosible:
    def test_con_pocos_ejercicios_se_pide_menos(self, hipertrofia):
        assert programacion.objetivo_por_musculo(hipertrofia, ejercicios=3, musculos=3) == 3

    def test_con_ocho_ejercicios_y_tres_musculos_sale_el_minimo_entero(self, hipertrofia):
        assert programacion.objetivo_por_musculo(hipertrofia, ejercicios=8, musculos=3) == 6

    def test_nunca_baja_de_una_serie(self, hipertrofia):
        assert programacion.objetivo_por_musculo(hipertrofia, ejercicios=1, musculos=5) == 1

    def test_sin_musculos_no_se_pide_nada(self, hipertrofia):
        assert programacion.objetivo_por_musculo(hipertrofia, ejercicios=6, musculos=0) == 0


class TestLoQueVeElModelo:
    def test_el_prompt_lleva_los_mismos_numeros_que_se_validan(self, hipertrofia):
        texto = programacion.describir(hipertrofia)

        assert "entre 3 y 4" in texto
        assert "6-20" in texto
        assert "120 s en los compuestos" in texto
        assert "al menos 6" in texto

    def test_el_resumen_cabe_en_una_linea(self, hipertrofia):
        assert programacion.resumen(hipertrofia) == (
            "3-4 series · 6-20 repeticiones · 120 s de descanso"
        )

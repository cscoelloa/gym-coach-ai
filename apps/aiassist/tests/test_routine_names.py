import pytest

from apps.aiassist.schemas import PlannedExercise, PlannedRoutine, RoutinePlan, ScheduledDay
from apps.aiassist.services.routine_generator import (
    _how_to_fix,
    resolve_routine_name,
    resolve_schedule,
    validate_plan,
)

DEFINIDAS = ["Empuje", "Tirón", "Día de Pierna"]


def plan(nombres_rutina, nombres_calendario):
    rutinas = [
        PlannedRoutine(
            name=nombre,
            exercises=[
                PlannedExercise(
                    external_id="0001", sets=3, reps_min=8, reps_max=12, rest_seconds=120
                )
            ],
        )
        for nombre in nombres_rutina
    ]
    calendario = [
        ScheduledDay(weekday=dia, routine_name=nombres_calendario[dia]) for dia in range(7)
    ]
    return RoutinePlan(
        name="Programa", description="x", routines=rutinas, schedule=calendario, rationale="x"
    )


class TestLoQueSeEmpareja:
    def test_el_nombre_exacto(self):
        assert resolve_routine_name("Empuje", DEFINIDAS) == "Empuje"

    def test_sin_tilde(self):
        assert resolve_routine_name("Tiron", DEFINIDAS) == "Tirón"

    def test_con_otras_mayusculas(self):
        assert resolve_routine_name("EMPUJE", DEFINIDAS) == "Empuje"

    def test_con_espacios_de_mas(self):
        assert resolve_routine_name("  Empuje  ", DEFINIDAS) == "Empuje"

    def test_la_version_corta_del_nombre(self):
        assert resolve_routine_name("Pierna", DEFINIDAS) == "Día de Pierna"

    def test_un_dia_de_descanso_no_es_un_fallo(self):
        assert resolve_routine_name("", DEFINIDAS) is None
        assert resolve_routine_name("   ", DEFINIDAS) is None


class TestDondeSePlanta:
    def test_un_nombre_que_no_se_parece_a_nada(self):
        assert resolve_routine_name("Cardio", DEFINIDAS) is None

    def test_si_encaja_con_dos_se_considera_no_resuelto(self):
        assert resolve_routine_name("Pierna", ["Pierna A", "Pierna B"]) is None

    def test_el_exacto_gana_aunque_otro_lo_contenga(self):
        assert resolve_routine_name("Pierna", ["Pierna", "Día de Pierna"]) == "Pierna"


class TestLaValidacionCompleta:
    def test_ya_no_falla_por_una_tilde(self, db):
        p = plan(["Empuje", "Tirón"], ["Empuje", "Tiron", "", "Empuje", "Tirón", "", ""])

        assert validate_plan(p, {"0001"}) == []

    def test_sigue_fallando_cuando_de_verdad_no_existe(self, db):
        p = plan(["Empuje"], ["Empuje", "Cardio", "", "", "", "", ""])

        problemas = validate_plan(p, {"0001"})

        assert any("Cardio" in x for x in problemas)

    def test_el_error_dice_cuales_SI_hay(self, db):
        p = plan(["Empuje"], ["Cardio", "", "", "", "", "", ""])

        problemas = validate_plan(p, {"0001"})

        assert any("«Empuje»" in x for x in problemas)


class TestElCalendarioSeResuelveUnaSolaVez:
    def test_validar_y_guardar_usan_la_misma_respuesta(self, db):
        p = plan(["Empuje", "Tirón"], ["Empuje", "Tiron", "", "Empuje", "Tirón", "", ""])

        asignado, sin_resolver = resolve_schedule(p)

        assert not sin_resolver
        assert asignado == {0: "Empuje", 1: "Tirón", 2: None, 3: "Empuje", 4: "Tirón",
                            5: None, 6: None}


class TestLaCorreccionApuntaAlFallo:
    def test_si_el_problema_son_los_nombres_se_le_habla_de_nombres(self):
        texto = _how_to_fix(["estos días apuntan a rutinas que no has definido: Pierna"])

        assert "copia el nombre de la rutina" in texto
        assert "identificadores" not in texto

    def test_si_el_problema_son_los_identificadores_se_le_habla_de_eso(self):
        texto = _how_to_fix(["estos identificadores no están en la lista de candidatos: 0012"])

        assert "identificadores" in texto
        assert "copia el nombre de la rutina" not in texto

    def test_con_los_dos_problemas_se_le_dicen_los_dos(self):
        texto = _how_to_fix([
            "estos días apuntan a rutinas que no has definido: Pierna",
            "estos identificadores no están en la lista de candidatos: 0012",
        ])

        assert "copia el nombre de la rutina" in texto
        assert "identificadores" in texto

    def test_nunca_se_queda_sin_decir_nada(self):
        assert _how_to_fix(["algo que no está en la tabla"])


@pytest.mark.parametrize("nombre", ["Empuje", "empuje", "EMPUJE", " Empuje ", "Empuje "])
def test_variantes_habituales_del_mismo_nombre(nombre):
    assert resolve_routine_name(nombre, ["Empuje"]) == "Empuje"


class TestElPromptPorDefecto:
    def test_no_pide_campos_que_el_esquema_no_tiene(self):
        from apps.aiassist.management.commands.seed_prompts import ROUTINE_SYSTEM
        from apps.aiassist.schemas import RoutinePlan, ScheduledDay

        campos = set(ScheduledDay.model_fields) | set(RoutinePlan.model_fields)

        assert "is_rest_day" not in ROUTINE_SYSTEM
        assert "is_rest_day" not in campos

    def test_explica_que_el_nombre_del_dia_tiene_que_coincidir(self):
        from apps.aiassist.management.commands.seed_prompts import ROUTINE_SYSTEM

        assert "routine_name" in ROUTINE_SYSTEM
        assert "carácter por carácter" in ROUTINE_SYSTEM

    def test_dice_como_se_marca_el_descanso(self):
        from apps.aiassist.management.commands.seed_prompts import ROUTINE_SYSTEM

        assert "vacío" in ROUTINE_SYSTEM

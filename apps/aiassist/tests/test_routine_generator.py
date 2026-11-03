from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.aiassist.models import (
    AIGeneration,
    AIProviderConfig,
    GenerationStatus,
    Provider,
    TrainingGoal,
)
from apps.aiassist.providers.base import ProviderResult
from apps.aiassist.schemas import PlannedExercise, PlannedRoutine, RoutinePlan, ScheduledDay
from apps.aiassist.services import GenerationFailed, apply_plan, generate_routine
from apps.aiassist.services.routine_generator import (
    MAX_ATTEMPTS,
    PER_EMPHASIS,
    PER_MUSCLE,
    select_candidates,
    validate_plan,
)
from apps.aiassist.services.split import DiaDelReparto
from apps.workouts.models import Exercise, MuscleGroup, Program, Routine

pytestmark = pytest.mark.django_db

User = get_user_model()
CLAVE = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def entorno(settings):
    settings.FIELD_ENCRYPTION_KEYS = [CLAVE]
    call_command("sync_metrics")
    call_command("seed_prompts")
    AIProviderConfig.objects.create(
        provider=Provider.ANTHROPIC, api_key="sk-de-prueba", is_active=True
    )


@pytest.fixture
def user():
    return User.objects.create_user(
        "atleta", password="Contrasena-Larga-1", goal="bulk", available_days_per_week=4
    )


@pytest.fixture
def catalogo():
    musculos = {
        slug: MuscleGroup.objects.create(slug=slug, name=nombre)
        for slug, nombre in [("pectorals", "Pectorales"), ("lats", "Dorsales"),
                             ("quads", "Cuádriceps")]
    }
    datos = [
        ("0001", "Press de banca", "chest", "barbell", "pectorals"),
        ("0002", "Press con mancuernas", "chest", "dumbbell", "pectorals"),
        ("0003", "Dominada", "back", "body weight", "lats"),
        ("0004", "Remo con barra", "back", "barbell", "lats"),
        ("0005", "Sentadilla", "upper legs", "barbell", "quads"),
        ("0006", "Prensa", "upper legs", "leverage machine", "quads"),
    ]
    return [
        Exercise.objects.create(
            external_id=ext, name=nombre, slug=ext, body_part=zona,
            equipment=equipo, target_muscle=musculos[musculo], is_global=True,
        )
        for ext, nombre, zona, equipo, musculo in datos
    ]


@pytest.fixture
def indice(catalogo):
    return {ex.external_id: ex for ex in catalogo}


def plan_valido(external_ids=("0001", "0003")) -> RoutinePlan:
    empuje = PlannedRoutine(
        name="Empuje",
        exercises=[
            PlannedExercise(
                external_id=ext, sets=3, reps_min=8, reps_max=12,
                rest_seconds=120,
            )
            for ext in external_ids
        ],
    )
    calendario = [
        ScheduledDay(weekday=dia, routine_name="Empuje" if dia < 4 else "")
        for dia in range(7)
    ]
    return RoutinePlan(
        name="Programa de prueba", description="Para probar",
        routines=[empuje], schedule=calendario, rationale="Porque sí",
    )


def resultado(plan) -> ProviderResult:
    return ProviderResult(
        parsed=plan, raw_text="{}", input_tokens=500, output_tokens=200, latency_ms=1200
    )


def configurar_proveedor(mock, *, supports_rag=False):
    mock.return_value.supports_rag = supports_rag
    mock.return_value.config.provider = "anthropic"
    mock.return_value.model = "claude-opus-5"
    return mock


@pytest.fixture
def generacion(user):
    def _crear(plan=None):
        plan = plan or plan_valido()
        return AIGeneration.objects.create(
            user=user, kind="routine", provider="anthropic", model="claude-opus-5",
            parsed_output=plan.model_dump(), status=GenerationStatus.OK,
        )

    return _crear


class TestCandidatos:
    def test_respeta_el_equipamiento_declarado(self, user, catalogo):
        user.available_equipment = ["barbell"]
        user.save()

        nombres = {ex.name for ex in select_candidates(user)}

        assert nombres == {"Press de banca", "Remo con barra", "Sentadilla"}

    def test_sin_equipamiento_declarado_entra_todo(self, user, catalogo):
        assert len(select_candidates(user)) == 6

    def test_reparte_entre_musculos_y_no_entre_zonas(self, user, catalogo):
        musculos = {ex.target_muscle.slug for ex in select_candidates(user)}

        assert musculos == {"pectorals", "lats", "quads"}

    def test_con_reparto_solo_entran_sus_musculos(self, user, catalogo):
        elegidos = select_candidates(user, muscles=["quads"])

        assert {ex.name for ex in elegidos} == {"Sentadilla", "Prensa"}

    def test_el_enfasis_se_lleva_mas_candidatos(self, user):
        musculo = MuscleGroup.objects.create(slug="quads", name="Cuádriceps")
        for numero in range(40):
            Exercise.objects.create(
                external_id=f"Q{numero:03}", name=f"Cuádriceps {numero:03}", slug=f"q{numero}",
                body_part="upper legs", equipment="barbell", target_muscle=musculo,
                is_global=True,
            )

        normal = select_candidates(user, muscles=["quads"])
        con_enfasis = select_candidates(user, muscles=["quads"], emphasis=["quads"])

        assert len(normal) == PER_MUSCLE
        assert len(con_enfasis) == PER_EMPHASIS

    def test_alterna_el_material_en_vez_de_vaciar_la_barra(self, user):
        musculo = MuscleGroup.objects.create(slug="lats", name="Dorsales")
        for material in ("barbell", "cable", "leverage machine"):
            for numero in range(20):
                Exercise.objects.create(
                    external_id=f"{material[:3]}{numero:03}",
                    name=f"{material} dorsal {numero:03}", slug=f"{material[:3]}-{numero}",
                    body_part="back", equipment=material, target_muscle=musculo, is_global=True,
                )

        materiales = {ex.equipment for ex in select_candidates(user, muscles=["lats"])}

        assert materiales == {"barbell", "cable", "leverage machine"}

    def test_colapsa_las_variantes_cosmeticas_del_catalogo(self, user, catalogo):
        musculo = MuscleGroup.objects.get(slug="quads")
        for sufijo in ("(male)", "(back pov)", "(side pov)"):
            Exercise.objects.create(
                external_id=f"S{sufijo}", name=f"Sentadilla {sufijo}", slug=f"sentadilla-{sufijo}",
                body_part="upper legs", equipment="barbell", target_muscle=musculo, is_global=True,
            )

        nombres = [ex.name for ex in select_candidates(user, muscles=["quads"])]

        assert nombres.count("Sentadilla") == 1
        assert not [n for n in nombres if "pov" in n or "male" in n]

    def test_lo_que_de_verdad_distingue_un_ejercicio_se_conserva(self, user, catalogo):
        musculo = MuscleGroup.objects.get(slug="quads")
        Exercise.objects.create(
            external_id="S-kneel", name="Sentadilla (kneeling)", slug="sentadilla-kneeling",
            body_part="upper legs", equipment="barbell", target_muscle=musculo, is_global=True,
        )

        nombres = {ex.name for ex in select_candidates(user, muscles=["quads"])}

        assert "Sentadilla (kneeling)" in nombres and "Sentadilla" in nombres

    def test_deja_fuera_el_cardio(self, user, catalogo):
        Exercise.objects.create(
            external_id="9999", name="Cinta", slug="cinta", body_part="cardio",
            equipment="stationary bike", is_cardio=True, is_global=True,
        )

        assert "Cinta" not in {ex.name for ex in select_candidates(user)}


class TestValidacion:
    def test_un_plan_correcto_no_tiene_problemas(self, indice):
        assert validate_plan(plan_valido(), indice) == []

    def test_detecta_identificadores_inventados(self, indice):
        problemas = validate_plan(plan_valido(("0001", "INVENTADO")), indice)

        assert any("no están en la lista" in p for p in problemas)

    def test_exige_los_siete_dias(self, indice):
        plan = plan_valido()
        plan.schedule = plan.schedule[:5]

        assert any("siete días" in p for p in validate_plan(plan, indice))

    def test_detecta_dias_repetidos(self, indice):
        plan = plan_valido()
        plan.schedule[1].weekday = 0

        assert any("siete días" in p for p in validate_plan(plan, indice))

    def test_rechaza_un_dia_que_apunta_a_una_rutina_inexistente(self, indice):
        plan = plan_valido()
        plan.schedule[0].routine_name = "Pierna"

        assert any("no has definido" in p for p in validate_plan(plan, indice))

    def test_rechaza_rutinas_con_el_mismo_nombre(self, indice):
        plan = plan_valido()
        plan.routines.append(plan.routines[0].model_copy(deep=True))

        assert any("mismo nombre" in p for p in validate_plan(plan, indice))

    def test_rechaza_una_rutina_sin_ejercicios(self, indice):
        plan = plan_valido()
        plan.routines[0].exercises = []

        assert any("no tiene ejercicios" in p for p in validate_plan(plan, indice))


def plan_de_dias(dias: dict[int, list[str]]) -> RoutinePlan:
    rutinas = [
        PlannedRoutine(
            name=f"Día {weekday}",
            exercises=[
                PlannedExercise(
                    external_id=ext, sets=3, reps_min=8, reps_max=12, rest_seconds=120
                )
                for ext in ejercicios
            ],
        )
        for weekday, ejercicios in sorted(dias.items())
    ]
    calendario = [
        ScheduledDay(weekday=dia, routine_name=f"Día {dia}" if dia in dias else "")
        for dia in range(7)
    ]
    return RoutinePlan(
        name="Programa", description="Para probar", routines=rutinas,
        schedule=calendario, rationale="Porque sí",
    )


def reparto(weekday, musculos, *, enfasis=None, ejercicios=2) -> DiaDelReparto:
    return DiaDelReparto(weekday, tuple(musculos), enfasis, ejercicios)


class TestValidacionDelReparto:
    def test_un_plan_que_cumple_el_reparto_no_tiene_problemas(self, indice):
        plan = plan_de_dias({0: ["0001", "0002"], 2: ["0005", "0006"]})
        split = [reparto(0, ["pectorals"]), reparto(2, ["quads"])]

        assert validate_plan(plan, indice, split=split) == []

    def test_detecta_un_dia_de_mas(self, indice):
        plan = plan_de_dias({0: ["0001", "0002"], 1: ["0003", "0004"]})
        split = [reparto(0, ["pectorals"])]

        problemas = validate_plan(plan, indice, split=split)

        assert any("no coinciden con el reparto" in p and "Martes" in p for p in problemas)

    def test_detecta_un_dia_que_falta(self, indice):
        plan = plan_de_dias({0: ["0001", "0002"]})
        split = [reparto(0, ["pectorals"]), reparto(3, ["quads"])]

        assert any("Jueves" in p for p in validate_plan(plan, indice, split=split))

    def test_exige_el_numero_exacto_de_ejercicios(self, indice):
        plan = plan_de_dias({0: ["0001", "0002"]})
        split = [reparto(0, ["pectorals"], ejercicios=8)]

        problemas = validate_plan(plan, indice, split=split)

        assert any("trae 2 ejercicios y el reparto pide 8" in p for p in problemas)

    def test_un_musculo_pedido_sin_ningun_ejercicio_suyo(self, indice):
        plan = plan_de_dias({0: ["0001", "0002"]})
        split = [reparto(0, ["pectorals", "lats"])]

        problemas = validate_plan(plan, indice, split=split)

        assert any("se queda sin ningún ejercicio de Dorsales" in p for p in problemas)

    def test_participar_de_refuerzo_no_cuenta_como_cubrir(self, indice, catalogo):
        biceps = MuscleGroup.objects.create(slug="biceps", name="Bíceps")
        remo = Exercise.objects.get(external_id="0004")
        remo.secondary_muscles.add(biceps)
        plan = plan_de_dias({0: ["0003", "0004"]})
        split = [reparto(0, ["lats", "biceps"])]

        problemas = validate_plan(plan, indice, split=split)

        assert any("sin ningún ejercicio de Bíceps" in p for p in problemas)

    def test_el_enfasis_necesita_al_menos_dos_ejercicios(self, indice):
        plan = plan_de_dias({0: ["0001", "0003", "0004"]})
        split = [reparto(0, ["pectorals", "lats"], enfasis="pectorals", ejercicios=3)]

        problemas = validate_plan(plan, indice, split=split)

        assert any("énfasis en Pectorales" in p for p in problemas)

    def test_el_enfasis_tiene_que_ser_el_que_mas_lleva(self, indice):
        plan = plan_de_dias({0: ["0001", "0002", "0003", "0004"]})
        split = [reparto(0, ["pectorals", "lats"], enfasis="pectorals", ejercicios=4)]

        assert validate_plan(plan, indice, split=split) == []

    def test_rechaza_el_mismo_musculo_dos_dias_seguidos(self, indice):
        plan = plan_de_dias({0: ["0001", "0002"], 1: ["0001", "0002"]})
        split = [reparto(0, ["pectorals"]), reparto(1, ["pectorals"])]

        problemas = validate_plan(plan, indice, split=split)

        assert any("días seguidos y repiten Pectorales" in p for p in problemas)

    def test_domingo_y_lunes_tambien_son_seguidos(self, indice):
        plan = plan_de_dias({0: ["0001", "0002"], 6: ["0001", "0002"]})
        split = [reparto(0, ["pectorals"]), reparto(6, ["pectorals"])]

        problemas = validate_plan(plan, indice, split=split)

        assert any("Domingo y Lunes" in p for p in problemas)

    def test_rechaza_el_mismo_ejercicio_dos_veces_en_la_misma_rutina(self, indice):
        plan = plan_de_dias({0: ["0001", "0001"]})

        assert any("repetido" in p for p in validate_plan(plan, indice))

    def test_con_identificadores_inventados_no_se_queja_del_reparto(self, indice):
        plan = plan_de_dias({0: ["0001", "NO_EXISTE"]})
        split = [reparto(0, ["pectorals"])]

        problemas = validate_plan(plan, indice, split=split)

        assert len(problemas) == 1
        assert "no están en la lista" in problemas[0]


class TestGeneracion:
    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_guarda_la_auditoria_pero_no_la_rutina(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        get_prov.return_value.generate_structured.return_value = resultado(plan_valido())

        generation = generate_routine(user)

        assert generation.status == GenerationStatus.OK
        assert generation.parsed_output["name"] == "Programa de prueba"
        assert Routine.objects.count() == 0

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_reintenta_una_vez_con_el_error_concreto(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        get_prov.return_value.generate_structured.side_effect = [
            resultado(plan_valido(("0001", "NO_EXISTE"))),
            resultado(plan_valido()),
        ]

        generation = generate_routine(user)

        assert generation.status == GenerationStatus.OK
        assert get_prov.return_value.generate_structured.call_count == 2
        segundo = get_prov.return_value.generate_structured.call_args_list[1].kwargs["user"]
        assert "NO_EXISTE" in segundo

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_se_rinde_tras_agotar_los_intentos(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        get_prov.return_value.generate_structured.return_value = resultado(
            plan_valido(("NO_EXISTE",))
        )

        with pytest.raises(GenerationFailed, match="no devolvió una rutina válida"):
            generate_routine(user)

        assert AIGeneration.objects.filter(status=GenerationStatus.ERROR).exists()
        assert get_prov.return_value.generate_structured.call_count == MAX_ATTEMPTS

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_al_rendirse_guarda_LO_QUE_DEVOLVIO_el_modelo(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        get_prov.return_value.generate_structured.return_value = resultado(
            plan_valido(("NO_EXISTE",))
        )

        with pytest.raises(GenerationFailed):
            generate_routine(user)

        fallida = AIGeneration.objects.get(status=GenerationStatus.ERROR)
        assert fallida.parsed_output, "la salida del modelo se ha vuelto a tirar"
        assert fallida.parsed_output["routines"][0]["exercises"][0]["external_id"] == "NO_EXISTE"

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_la_correccion_apunta_al_fallo_que_hubo(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        mal = plan_valido()
        mal.schedule[0].routine_name = "Cardio"
        get_prov.return_value.generate_structured.side_effect = [
            resultado(mal), resultado(plan_valido()),
        ]

        generate_routine(user)

        segundo = get_prov.return_value.generate_structured.call_args_list[1].kwargs["user"]
        assert "copia el nombre de la rutina" in segundo


    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_con_reparto_el_prompt_lo_lleva_y_la_auditoria_lo_guarda(
        self, get_prov, user, catalogo
    ):
        configurar_proveedor(get_prov)
        plan = plan_de_dias({0: ["0001", "0002"]})
        get_prov.return_value.generate_structured.return_value = resultado(plan)
        split = [reparto(0, ["pectorals"], ejercicios=2)]

        generacion = generate_routine(user, split=split)

        mensaje = get_prov.return_value.generate_structured.call_args.kwargs["user"]
        assert "Lunes: Pectorales — exactamente 2 ejercicios" in mensaje
        assert "Domingo: DESCANSO" in mensaje
        assert generacion.request_params["reparto"][0]["muscles"] == ["pectorals"]

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_con_reparto_los_candidatos_son_solo_sus_musculos(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        get_prov.return_value.generate_structured.return_value = resultado(
            plan_de_dias({0: ["0005", "0006"]})
        )

        generate_routine(user, split=[reparto(0, ["quads"], ejercicios=2)])

        mensaje = get_prov.return_value.generate_structured.call_args.kwargs["user"]
        assert "Sentadilla" in mensaje and "Press de banca" not in mensaje

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_un_plan_que_ignora_el_reparto_se_reintenta_con_el_fallo(
        self, get_prov, user, catalogo
    ):
        configurar_proveedor(get_prov)
        get_prov.return_value.generate_structured.side_effect = [
            resultado(plan_de_dias({0: ["0001"]})),
            resultado(plan_de_dias({0: ["0001", "0003"]})),
        ]
        split = [reparto(0, ["pectorals", "lats"], ejercicios=2)]

        generacion = generate_routine(user, split=split)

        assert generacion.status == GenerationStatus.OK
        segundo = get_prov.return_value.generate_structured.call_args_list[1].kwargs["user"]
        assert "sin ningún ejercicio de Dorsales" in segundo
        assert "músculo OBJETIVO sea ese" in segundo

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_el_prompt_lleva_la_programacion_del_objetivo(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        pesado = plan_valido()
        for item in pesado.routines[0].exercises:
            item.reps_min, item.reps_max = 4, 6
        get_prov.return_value.generate_structured.return_value = resultado(pesado)

        generate_routine(user, training_goal=TrainingGoal.STRENGTH)

        mensaje = get_prov.return_value.generate_structured.call_args.kwargs["user"]
        assert "Objetivo del entrenamiento: Fuerza" in mensaje
        assert "180 s en los compuestos" in mensaje

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_una_rutina_floja_se_reintenta_con_el_numero_concreto(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        floja = plan_valido()
        for item in floja.routines[0].exercises:
            item.sets = 1
            item.rest_seconds = 60
        get_prov.return_value.generate_structured.side_effect = [
            resultado(floja), resultado(plan_valido()),
        ]

        generacion = generate_routine(user)

        assert generacion.status == GenerationStatus.OK
        segundo = get_prov.return_value.generate_structured.call_args_list[1].kwargs["user"]
        assert "lleva 1 series" in segundo
        assert "descansa 60 s" in segundo
        assert "Ajusta las series de cada ejercicio" in segundo

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_el_objetivo_queda_en_la_auditoria(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        largo = plan_valido()
        for item in largo.routines[0].exercises:
            item.reps_min, item.reps_max = 15, 20
        get_prov.return_value.generate_structured.return_value = resultado(largo)

        generacion = generate_routine(user, training_goal=TrainingGoal.ENDURANCE)

        assert generacion.request_params["objetivo_de_entreno"] == TrainingGoal.ENDURANCE

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_los_libros_solo_en_el_primer_intento(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov, supports_rag=True)
        with patch(
            "apps.aiassist.services.routine_generator.active_vector_store_ids",
            return_value=["vs_1"],
        ):
            get_prov.return_value.generate_structured.side_effect = [
                resultado(plan_valido(("NO_EXISTE",))), resultado(plan_valido()),
            ]

            generate_routine(user)

        llamadas = get_prov.return_value.generate_structured.call_args_list
        assert llamadas[0].kwargs["vector_store_ids"] == ["vs_1"]
        assert llamadas[1].kwargs["vector_store_ids"] is None

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_solo_pasa_almacenes_si_el_proveedor_soporta_rag(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov, supports_rag=False)
        get_prov.return_value.generate_structured.return_value = resultado(plan_valido())

        generate_routine(user)

        kwargs = get_prov.return_value.generate_structured.call_args.kwargs
        assert kwargs["vector_store_ids"] is None

    @patch("apps.aiassist.services.routine_generator.get_provider")
    def test_sin_ejercicios_compatibles_lo_dice_claro(self, get_prov, user, catalogo):
        configurar_proveedor(get_prov)
        user.available_equipment = ["tire"]
        user.save()

        with pytest.raises(GenerationFailed, match="equipamiento"):
            generate_routine(user)


class TestAplicar:
    def test_crea_los_siete_dias(self, generacion, catalogo):
        program = apply_plan(generacion())

        assert program.schedule.count() == 7
        assert sorted(program.schedule.values_list("weekday", flat=True)) == list(range(7))

    def test_enlaza_el_programa_con_su_generacion(self, generacion, catalogo):
        gen = generacion()

        program = apply_plan(gen)

        assert program.generation == gen
        assert program.source == Program.Source.AI

    def test_una_sola_rutina_asignada_a_varios_dias(self, generacion, catalogo):
        program = apply_plan(generacion())

        assert Routine.objects.filter(user=program.user).count() == 1

        rutina = Routine.objects.get(user=program.user)
        dias = program.schedule.filter(routine=rutina)
        assert dias.count() == 4
        assert sorted(dias.values_list("weekday", flat=True)) == [0, 1, 2, 3]

    def test_resuelve_los_ejercicios_por_identificador(self, generacion, catalogo):
        program = apply_plan(generacion())

        rutina = program.schedule.get(weekday=0).routine
        nombres = set(rutina.exercises.values_list("exercise__name", flat=True))
        assert nombres == {"Press de banca", "Dominada"}

    def test_completa_como_descanso_los_dias_que_falten(self, generacion, catalogo):
        plan = plan_valido()
        plan.schedule = plan.schedule[:4]

        program = apply_plan(generacion(plan))

        assert program.schedule.count() == 7
        assert program.schedule.filter(routine__isnull=True).count() == 3

    def test_acota_valores_disparatados(self, generacion, catalogo):
        plan = plan_valido()
        plan.routines[0].exercises[0].sets = 99
        plan.routines[0].exercises[0].rest_seconds = 99999

        program = apply_plan(generacion(plan))

        item = program.schedule.get(weekday=0).routine.exercises.first()
        assert item.target_sets == 20
        assert item.rest_seconds == 900

    def test_no_se_puede_aplicar_dos_veces(self, generacion, catalogo):
        gen = generacion()
        apply_plan(gen)

        with pytest.raises(GenerationFailed, match="ya se aplicó"):
            apply_plan(gen)

    def test_activar_el_nuevo_desactiva_los_demas(self, user, generacion, catalogo):
        vieja = Program.objects.create(user=user, name="Anterior", is_active=True)

        apply_plan(generacion())

        vieja.refresh_from_db()
        assert vieja.is_active is False


class TestCompatibilidadDelEsquema:
    def test_un_plan_guardado_con_campos_de_mas_sigue_validando(self):
        crudo = {
            "name": "Programa viejo",
            "description": "Guardado con el formato antiguo",
            "routines": [{
                "name": "Empuje",
                "exercises": [{
                    "external_id": "0001", "sets": 3, "reps_min": 8, "reps_max": 12,
                    "rest_seconds": 120,
                    "rpe": 8.0, "notes": "baja controlado",
                }],
            }],
            "schedule": [
                {"weekday": d, "routine_name": "Empuje" if d == 0 else ""} for d in range(7)
            ],
            "rationale": "Porque sí",
        }

        plan = RoutinePlan.model_validate(crudo)

        assert plan.routines[0].exercises[0].sets == 3
        assert not hasattr(plan.routines[0].exercises[0], "rpe")

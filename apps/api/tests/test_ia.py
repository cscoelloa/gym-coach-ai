from datetime import date, timedelta
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from apps.aiassist.models import (
    AIGeneration,
    AIProviderConfig,
    GenerationKind,
    GenerationStatus,
    Provider,
)
from apps.aiassist.providers import ProviderError
from apps.aiassist.providers.base import ProviderResult
from apps.aiassist.schemas import (
    PlannedExercise,
    PlannedRoutine,
    ProgressAnalysis,
    ProposedChange,
    RoutinePlan,
    ScheduledDay,
    StalledExercise,
)
from apps.aiassist.services.progress_analyzer import MIN_SESSIONS
from apps.workouts.models import Exercise, MuscleGroup, Program, WorkoutSession

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
def ana():
    return User.objects.create_user(
        "ana", password="Contrasena-Larga-Api-1", goal="bulk", available_days_per_week=4
    )


@pytest.fixture
def beto():
    return User.objects.create_user("beto", password="Contrasena-Larga-Api-1")


@pytest.fixture
def api(ana):
    cliente = APIClient()
    cliente.force_login(ana)
    return cliente


@pytest.fixture
def catalogo():
    pecho = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    nombres = ["Press de banca", "Remo con barra", "Aperturas", "Fondos"]
    return [
        Exercise.objects.create(
            external_id=f"000{n}", name=nombre, slug=f"ej-{n}", body_part="chest",
            equipment="barbell", target_muscle=pecho, is_global=True,
        )
        for n, nombre in enumerate(nombres, start=1)
    ]


def plan(external_ids=("0001", "0002")) -> RoutinePlan:
    return RoutinePlan(
        name="Empuje/Tirón",
        description="Para ganar masa en cuatro días.",
        routines=[
            PlannedRoutine(
                name="Empuje",
                exercises=[
                    PlannedExercise(
                        external_id=eid, sets=4, reps_min=6, reps_max=8, rest_seconds=150
                    )
                    for eid in external_ids
                ],
            )
        ],
        schedule=[
            ScheduledDay(weekday=dia, routine_name="Empuje" if dia in (0, 3) else "")
            for dia in range(7)
        ],
        rationale="Dos empujes por semana con volumen moderado.",
    )


def analisis() -> ProgressAnalysis:
    return ProgressAnalysis(
        summary="Vas bien en general.",
        patterns=["Volumen estable"],
        stalled=[
            StalledExercise(exercise="Press de banca", weeks_stalled=6, likely_cause="poco volumen")
        ],
        recommendations=["Sube una serie en press"],
        proposed_changes=[
            ProposedChange(target="Lunes", change="Añadir una serie", reason="Estancamiento")
        ],
        data_caveats=["Sin RPE no se puede juzgar la intensidad."],
    )


def resultado(parsed):
    return ProviderResult(
        parsed=parsed,
        raw_text='{"secreto": "esto es la respuesta cruda"}',
        input_tokens=800,
        output_tokens=300,
        latency_ms=2000,
    )


def falso_proveedor(mock, parsed):
    mock.return_value.supports_rag = False
    mock.return_value.config.provider = "anthropic"
    mock.return_value.model = "claude-opus-5"
    mock.return_value.generate_structured.return_value = resultado(parsed)
    return mock


def generar(api, **datos):
    with patch("apps.aiassist.services.routine_generator.get_provider") as proveedor:
        falso_proveedor(proveedor, plan())
        return api.post(reverse("api-ia-generar"), datos, format="json")


class TestGenerarUnaRutina:
    def test_devuelve_la_propuesta_sin_crear_nada(self, api, ana, catalogo):
        respuesta = generar(api, days_per_week=4)

        assert respuesta.status_code == 201
        assert respuesta.json()["nombre"] == "Empuje/Tirón"
        assert not Program.objects.exists()
        assert AIGeneration.objects.filter(user=ana, kind=GenerationKind.ROUTINE).count() == 1

    def test_los_ejercicios_llegan_resueltos_contra_el_catalogo(self, api, catalogo):
        rutina = generar(api).json()["rutinas"][0]

        assert [e["nombre"] for e in rutina["ejercicios"]] == [
            "Press de banca", "Remo con barra"
        ]
        assert all(e["en_catalogo"] for e in rutina["ejercicios"])

    def test_un_ejercicio_que_ya_no_esta_en_el_catalogo_se_marca_en_vez_de_desaparecer(
        self, api, ana, catalogo
    ):
        vieja = AIGeneration.objects.create(
            user=ana, kind=GenerationKind.ROUTINE, status=GenerationStatus.OK,
            provider="anthropic", model="claude-opus-5",
            parsed_output=plan(external_ids=("0001", "9999")).model_dump(),
        )

        datos = api.get(reverse("api-ia-propuesta", args=[vieja.pk])).json()

        ejercicios = datos["rutinas"][0]["ejercicios"]
        assert ejercicios[0]["en_catalogo"] is True
        assert ejercicios[1]["en_catalogo"] is False
        assert ejercicios[1]["nombre"] == "9999"

    def test_la_semana_trae_los_siete_dias(self, api, catalogo):
        semana = generar(api).json()["semana"]

        assert [d["weekday"] for d in semana] == [0, 1, 2, 3, 4, 5, 6]
        assert semana[0]["rutina"] == "Empuje"
        assert semana[1]["rutina"] is None

    def test_no_se_filtra_el_prompt_ni_la_respuesta_cruda(self, api, catalogo):
        cuerpo = generar(api, notes="me duele el hombro derecho").content.decode()

        assert "prompt" not in cuerpo
        assert "raw_response" not in cuerpo
        assert "esto es la respuesta cruda" not in cuerpo
        assert "hombro" not in cuerpo

    def test_el_formulario_avisa_si_falta_el_equipamiento(self, api, ana):
        datos = api.get(reverse("api-ia-generar")).json()

        assert datos["tiene_equipamiento"] is False
        assert datos["dias_por_defecto"] == 4
        assert datos["restantes"] > 0

    def test_el_objetivo_de_entreno_llega_al_generador(self, api, catalogo):
        with patch("apps.api.ia.generate_routine") as generar:
            generar.return_value = AIGeneration.objects.create(
                user=None, kind=GenerationKind.ROUTINE, provider="anthropic",
                model="claude-opus-5", status=GenerationStatus.OK,
                parsed_output=plan().model_dump(),
            )
            api.post(
                reverse("api-ia-generar"), {"training_goal": "strength"}, format="json"
            )

        assert generar.call_args.kwargs["training_goal"] == "strength"

    def test_un_objetivo_inventado_se_rechaza(self, api, catalogo):
        respuesta = api.post(
            reverse("api-ia-generar"), {"training_goal": "crossfit"}, format="json"
        )

        assert respuesta.status_code == 400
        assert respuesta.json()["codigo"] == "parametros"
        assert not AIGeneration.objects.exists()

    def test_el_formulario_dice_qué_implica_cada_objetivo(self, api):
        datos = api.get(reverse("api-ia-generar")).json()

        assert datos["objetivo_por_defecto"] == "hypertrophy"
        hipertrofia = next(o for o in datos["objetivos"] if o["valor"] == "hypertrophy")
        assert "3-4 series" in hipertrofia["resumen"]

    def test_el_formulario_ofrece_los_musculos_entrenables(self, api, catalogo):
        datos = api.get(reverse("api-ia-generar")).json()

        assert {"valor": "pectorals", "etiqueta": "Pectorales", "n": 4} in datos["musculos"]
        assert datos["dias_sugeridos"] == [0, 1, 3, 4]
        assert datos["ejercicios"]["max"] == 10

    def test_el_reparto_llega_al_generador_y_queda_en_la_auditoria(self, api, catalogo):
        cuatro = ("0001", "0002", "0003", "0004")
        with patch("apps.aiassist.services.routine_generator.get_provider") as proveedor:
            falso_proveedor(proveedor, plan(external_ids=cuatro))
            respuesta = api.post(
                reverse("api-ia-generar"),
                {"split": [
                    {"weekday": 0, "muscles": ["pectorals"], "emphasis": None, "exercises": 4},
                    {"weekday": 3, "muscles": ["pectorals"], "emphasis": None, "exercises": 4},
                ]},
                format="json",
            )
            mensaje = proveedor.return_value.generate_structured.call_args.kwargs["user"]

        assert respuesta.status_code == 201
        assert "Lunes: Pectorales — exactamente 4 ejercicios" in mensaje
        assert AIGeneration.objects.get().request_params["reparto"][0]["weekday"] == 0

    def test_un_reparto_imposible_se_rechaza_sin_llamar_al_modelo(self, api, catalogo):
        respuesta = api.post(
            reverse("api-ia-generar"),
            {"split": [{"weekday": 0, "muscles": ["inventado"], "exercises": 4}]},
            format="json",
        )

        assert respuesta.status_code == 400
        assert respuesta.json()["codigo"] == "reparto"
        assert not AIGeneration.objects.exists()

    def test_repetir_musculo_en_dias_seguidos_se_avisa_antes_de_generar(self, api, catalogo):
        respuesta = api.post(
            reverse("api-ia-generar"),
            {"split": [
                {"weekday": 0, "muscles": ["pectorals"], "exercises": 4},
                {"weekday": 1, "muscles": ["pectorals"], "exercises": 4},
            ]},
            format="json",
        )

        assert respuesta.status_code == 400
        assert respuesta.json()["codigo"] == "descanso"
        assert "Lunes y Martes" in respuesta.json()["detail"]
        assert not AIGeneration.objects.exists()

    @pytest.mark.parametrize("dias", [0, 8, -2])
    def test_un_numero_de_dias_imposible_se_rechaza(self, api, catalogo, dias):
        respuesta = api.post(
            reverse("api-ia-generar"), {"days_per_week": dias}, format="json"
        )

        assert respuesta.status_code == 400
        assert respuesta.json()["codigo"] == "parametros"
        assert not AIGeneration.objects.exists()

    def test_las_notas_se_recortan_antes_de_enviarse(self, api, catalogo):
        with patch("apps.aiassist.services.routine_generator.get_provider") as proveedor:
            falso_proveedor(proveedor, plan())
            api.post(
                reverse("api-ia-generar"), {"notes": "x" * 5000}, format="json"
            )
            llamada = proveedor.return_value.generate_structured.call_args

        assert "x" * 1001 not in str(llamada)


class TestElCupo:
    def test_agotado_responde_429_y_no_llama_al_modelo(self, api, ana, catalogo, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 1
        generar(api)

        with patch("apps.aiassist.services.routine_generator.get_provider") as proveedor:
            respuesta = api.post(reverse("api-ia-generar"), {}, format="json")
            proveedor.assert_not_called()

        assert respuesta.status_code == 429
        assert respuesta.json()["codigo"] == "cuota"

    def test_un_fallo_del_proveedor_no_gasta_cupo(self, api, ana, catalogo, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 2
        antes = api.get(reverse("api-ia-generar")).json()["restantes"]

        with patch("apps.aiassist.services.routine_generator.get_provider") as proveedor:
            proveedor.return_value.generate_structured.side_effect = ProviderError("caído")
            proveedor.return_value.config.provider = "anthropic"
            proveedor.return_value.model = "claude-opus-5"
            proveedor.return_value.supports_rag = False
            respuesta = api.post(reverse("api-ia-generar"), {}, format="json")

        assert respuesta.status_code == 502
        assert respuesta.json()["codigo"] == "proveedor"
        assert api.get(reverse("api-ia-generar")).json()["restantes"] == antes

    def test_sin_ejercicios_que_encajen_lo_dice_en_vez_de_llamar(self, api):
        with patch("apps.aiassist.services.routine_generator.get_provider") as proveedor:
            respuesta = api.post(reverse("api-ia-generar"), {}, format="json")
            proveedor.assert_not_called()

        assert respuesta.status_code == 409
        assert respuesta.json()["codigo"] == "sin_candidatos"


class TestLaPropuesta:
    def test_se_puede_volver_a_pedir_para_recargar_la_pantalla(self, api, catalogo):
        pk = generar(api).json()["generacion"]["id"]

        datos = api.get(reverse("api-ia-propuesta", args=[pk])).json()

        assert datos["nombre"] == "Empuje/Tirón"
        assert datos["ya_aplicada"] is False

    def test_no_se_ve_la_propuesta_de_otra_persona(self, api, beto, catalogo):
        ajena = AIGeneration.objects.create(
            user=beto, kind=GenerationKind.ROUTINE, status=GenerationStatus.OK,
            provider="anthropic", model="claude-opus-5",
            parsed_output=plan().model_dump(),
        )

        respuesta = api.get(reverse("api-ia-propuesta", args=[ajena.pk]))

        assert respuesta.status_code == 404

    def test_trae_lo_que_costo_la_llamada(self, api, catalogo):
        metadatos = generar(api).json()["generacion"]

        assert metadatos["tokens_entrada"] == 800
        assert metadatos["tokens_salida"] == 300
        assert metadatos["modelo"] == "claude-opus-5"


class TestAceptarYDescartar:
    def test_aceptar_crea_el_programa_con_sus_rutinas_y_su_semana(self, api, ana, catalogo):
        pk = generar(api).json()["generacion"]["id"]

        respuesta = api.post(reverse("api-ia-aceptar", args=[pk]))

        assert respuesta.status_code == 201
        programa = Program.objects.get(user=ana)
        assert respuesta.json()["programa"]["id"] == programa.pk
        assert programa.schedule.count() == 7
        assert programa.schedule.filter(routine__isnull=False).count() == 2

    def test_aceptar_dos_veces_no_duplica_el_programa(self, api, ana, catalogo):
        pk = generar(api).json()["generacion"]["id"]
        api.post(reverse("api-ia-aceptar", args=[pk]))

        respuesta = api.post(reverse("api-ia-aceptar", args=[pk]))

        assert respuesta.status_code == 409
        assert Program.objects.filter(user=ana).count() == 1

    def test_la_propuesta_aceptada_lo_dice(self, api, catalogo):
        pk = generar(api).json()["generacion"]["id"]
        api.post(reverse("api-ia-aceptar", args=[pk]))

        assert api.get(reverse("api-ia-propuesta", args=[pk])).json()["ya_aplicada"] is True

    def test_no_se_acepta_la_propuesta_de_otra_persona(self, api, beto, catalogo):
        ajena = AIGeneration.objects.create(
            user=beto, kind=GenerationKind.ROUTINE, status=GenerationStatus.OK,
            provider="anthropic", model="claude-opus-5",
            parsed_output=plan().model_dump(),
        )

        respuesta = api.post(reverse("api-ia-aceptar", args=[ajena.pk]))

        assert respuesta.status_code == 404
        assert not Program.objects.exists()

    def test_descartar_conserva_la_fila_de_auditoria(self, api, catalogo):
        pk = generar(api).json()["generacion"]["id"]

        respuesta = api.post(reverse("api-ia-descartar", args=[pk]))

        assert respuesta.status_code == 204
        assert AIGeneration.objects.filter(pk=pk).exists()

    def test_aceptar_exige_post(self, api, catalogo):
        pk = generar(api).json()["generacion"]["id"]

        assert api.get(reverse("api-ia-aceptar", args=[pk])).status_code == 405
        assert not Program.objects.exists()


class TestElAnalisisDeProgreso:
    def sesiones(self, user, cuantas):
        for dia in range(cuantas):
            WorkoutSession.objects.create(user=user, date=date.today() - timedelta(days=dia * 3))

    def test_sin_analisis_dice_cuanto_falta_para_poder_pedirlo(self, api, ana):
        self.sesiones(ana, 2)

        datos = api.get(reverse("api-ia-analisis")).json()

        assert datos["analisis"] is None
        assert datos["sesiones"] == 2
        assert datos["sesiones_necesarias"] == MIN_SESSIONS

    def test_sin_historial_suficiente_responde_409_y_no_llama_al_modelo(self, api, ana):
        self.sesiones(ana, MIN_SESSIONS - 1)

        with patch("apps.aiassist.services.progress_analyzer.get_provider") as proveedor:
            respuesta = api.post(reverse("api-ia-analisis"))
            proveedor.assert_not_called()

        assert respuesta.status_code == 409
        assert respuesta.json()["codigo"] == "sin_datos"

    def test_con_historial_analiza_y_devuelve_el_resultado(self, api, ana):
        self.sesiones(ana, MIN_SESSIONS)

        with patch("apps.aiassist.services.progress_analyzer.get_provider") as proveedor:
            falso_proveedor(proveedor, analisis())
            respuesta = api.post(reverse("api-ia-analisis"))

        datos = respuesta.json()
        assert respuesta.status_code == 201
        assert datos["analisis"]["summary"] == "Vas bien en general."
        assert datos["analisis"]["stalled"][0]["exercise"] == "Press de banca"
        assert datos["analisis"]["data_caveats"]

    def test_el_get_devuelve_el_ultimo_analisis(self, api, ana):
        self.sesiones(ana, MIN_SESSIONS)
        with patch("apps.aiassist.services.progress_analyzer.get_provider") as proveedor:
            falso_proveedor(proveedor, analisis())
            api.post(reverse("api-ia-analisis"))

        datos = api.get(reverse("api-ia-analisis")).json()

        assert datos["analisis"]["summary"] == "Vas bien en general."
        assert datos["generacion"]["modelo"] == "claude-opus-5"

    def test_el_analisis_tampoco_filtra_el_texto_crudo(self, api, ana):
        self.sesiones(ana, MIN_SESSIONS)
        with patch("apps.aiassist.services.progress_analyzer.get_provider") as proveedor:
            falso_proveedor(proveedor, analisis())
            api.post(reverse("api-ia-analisis"))

        cuerpo = api.get(reverse("api-ia-analisis")).content.decode()

        assert "esto es la respuesta cruda" not in cuerpo
        assert "prompt_rendered" not in cuerpo

    def test_no_se_ve_el_analisis_de_otra_persona(self, api, beto):
        AIGeneration.objects.create(
            user=beto, kind=GenerationKind.PROGRESS, status=GenerationStatus.OK,
            provider="anthropic", model="claude-opus-5",
            parsed_output=analisis().model_dump(),
        )

        assert api.get(reverse("api-ia-analisis")).json()["analisis"] is None

    def test_agotado_el_cupo_responde_429(self, api, ana, settings):
        settings.AI_RATE_LIMIT_ANALYSIS_PER_HOUR = 1
        self.sesiones(ana, MIN_SESSIONS)
        with patch("apps.aiassist.services.progress_analyzer.get_provider") as proveedor:
            falso_proveedor(proveedor, analisis())
            api.post(reverse("api-ia-analisis"))

            respuesta = api.post(reverse("api-ia-analisis"))

        assert respuesta.status_code == 429
        assert respuesta.json()["codigo"] == "cuota"


class TestSinSesion:
    @pytest.mark.parametrize("nombre", ["api-ia-generar", "api-ia-analisis"])
    def test_hay_que_identificarse(self, nombre):
        assert APIClient().get(reverse(nombre)).status_code in (401, 403)

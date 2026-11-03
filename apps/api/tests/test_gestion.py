from datetime import timedelta
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.aiassist import rag
from apps.aiassist.models import (
    AIGeneration,
    AIProviderConfig,
    DocumentStatus,
    GenerationKind,
    GenerationStatus,
    KnowledgeDocument,
    ProgrammingRules,
    PromptKey,
    PromptTemplate,
    Provider,
    TrainingGoal,
    VectorStore,
)
from apps.aiassist.providers import ProviderError
from apps.aiassist.providers.base import ProviderResult
from apps.aiassist.schemas import ConnectionTest
from apps.aiassist.services import programacion
from apps.metrics.models import Metric, UserMetricPreference
from apps.workouts.models import Exercise, MuscleGroup

pytestmark = pytest.mark.django_db

User = get_user_model()
CLAVE = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def entorno(settings):
    settings.FIELD_ENCRYPTION_KEYS = [CLAVE]


@pytest.fixture
def jefa():
    return User.objects.create_user(
        "jefa", password="Contrasena-Larga-Admin-1", is_staff=True, is_superuser=True
    )


@pytest.fixture
def socia():
    return User.objects.create_user("socia", password="Contrasena-Larga-Api-1")


@pytest.fixture
def api(jefa):
    cliente = APIClient()
    cliente.force_login(jefa)
    return cliente


@pytest.fixture
def proveedor():
    return AIProviderConfig.objects.create(
        provider=Provider.ANTHROPIC, api_key="sk-secreta-de-verdad-1234", is_active=True
    )


SUELTAS = ["api-gestion-resumen", "api-gestion-catalogo"]


def rutas_del_panel() -> list[str]:
    from apps.api.urls import gestion_router

    return [f"{basename}-list" for _, _, basename in gestion_router.registry]


class TestSoloElStaffEntra:
    @pytest.mark.parametrize("nombre", rutas_del_panel() + SUELTAS)
    def test_una_usuaria_normal_no_puede_ni_mirar(self, socia, nombre):
        cliente = APIClient()
        cliente.force_login(socia)

        respuesta = cliente.get(reverse(nombre))

        assert respuesta.status_code == 403, f"«{nombre}» deja entrar a quien no es staff"

    @pytest.mark.parametrize("nombre", rutas_del_panel() + SUELTAS)
    def test_sin_sesion_tampoco(self, nombre, db):
        assert APIClient().get(reverse(nombre)).status_code in (401, 403)

    @pytest.mark.parametrize("nombre", rutas_del_panel() + SUELTAS)
    def test_el_staff_sí(self, api, nombre):
        assert api.get(reverse(nombre)).status_code == 200

    def test_el_router_del_panel_no_se_ha_quedado_vacio(self):
        assert len(rutas_del_panel()) >= 7


class TestLosProveedores:
    def test_la_clave_no_sale_nunca(self, api, proveedor):
        cuerpo = api.get(reverse("api-gestion-proveedor-list")).content.decode()

        assert "sk-secreta-de-verdad-1234" not in cuerpo
        assert '"api_key"' not in cuerpo

    def test_lo_que_sale_es_la_version_enmascarada(self, api, proveedor):
        datos = api.get(reverse("api-gestion-proveedor-list")).json()[0]

        assert datos["masked_api_key"].endswith("1234")
        assert "secreta" not in datos["masked_api_key"]
        assert datos["has_usable_key"] is True

    def test_se_puede_cambiar_el_modelo_sin_volver_a_pegar_la_clave(self, api, proveedor):
        respuesta = api.patch(
            reverse("api-gestion-proveedor-detail", args=[proveedor.pk]),
            {"max_tokens": 8000},
            format="json",
        )

        assert respuesta.status_code == 200
        proveedor.refresh_from_db()
        assert proveedor.max_tokens == 8000
        assert proveedor.api_key == "sk-secreta-de-verdad-1234"

    def test_crear_una_sin_clave_se_rechaza(self, api):
        respuesta = api.post(
            reverse("api-gestion-proveedor-list"),
            {"provider": Provider.ANTHROPIC, "is_active": True},
            format="json",
        )

        assert respuesta.status_code == 400
        assert "api_key" in respuesta.json()

    def test_activar_una_desactiva_las_demas(self, api, proveedor):
        respuesta = api.post(
            reverse("api-gestion-proveedor-list"),
            {"provider": Provider.OPENAI, "model": "gpt-5",
             "api_key": "sk-otra", "is_active": True},
            format="json",
        )

        assert respuesta.status_code == 201
        proveedor.refresh_from_db()
        assert proveedor.is_active is False
        assert AIProviderConfig.objects.filter(is_active=True).count() == 1

    def test_probar_hace_una_llamada_de_verdad_y_la_anota(self, api, proveedor):
        with patch("apps.api.gestion.get_provider") as doble:
            doble.return_value.generate_structured.return_value = ProviderResult(
                parsed=ConnectionTest(ok=True, message="Hola"),
                raw_text="{}", input_tokens=10, output_tokens=5, latency_ms=800,
            )
            respuesta = api.post(reverse("api-gestion-proveedor-probar", args=[proveedor.pk]))

        assert respuesta.status_code == 200
        assert respuesta.json() == {
            "ok": True, "latencia_ms": 800, "tokens": 15, "modelo": "claude-opus-5",
        }
        assert AIGeneration.objects.filter(kind=GenerationKind.TEST).count() == 1

    def test_una_clave_mala_lo_dice_y_queda_registrada(self, api, proveedor):
        with patch("apps.api.gestion.get_provider") as doble:
            doble.return_value.generate_structured.side_effect = ProviderError("401 unauthorized")
            respuesta = api.post(reverse("api-gestion-proveedor-probar", args=[proveedor.pk]))

        assert respuesta.status_code == 502
        assert respuesta.json()["ok"] is False
        registrada = AIGeneration.objects.get(kind=GenerationKind.TEST)
        assert registrada.status == GenerationStatus.ERROR

    def test_probar_no_tumba_el_panel_si_el_sdk_revienta(self, api, proveedor):
        with patch("apps.api.gestion.get_provider") as doble:
            doble.side_effect = TypeError("algo raro")
            respuesta = api.post(reverse("api-gestion-proveedor-probar", args=[proveedor.pk]))

        assert respuesta.status_code == 502
        assert "inesperado" in respuesta.json()["detail"]


@pytest.fixture
def prompt():
    call_command("seed_prompts")
    return PromptTemplate.objects.filter(key=PromptKey.ROUTINE_GENERATION).first()


class TestLosPrompts:
    def test_trae_las_variables_disponibles(self, api, prompt):
        datos = api.get(reverse("api-gestion-prompt-detail", args=[prompt.pk])).json()

        assert "perfil" in datos["available_variables"]
        assert "candidatos" in datos["available_variables"]

    def test_una_plantilla_rota_no_se_guarda(self, api, prompt):
        respuesta = api.patch(
            reverse("api-gestion-prompt-detail", args=[prompt.pk]),
            {"user_template": "{% if %}roto"},
            format="json",
        )

        assert respuesta.status_code == 400
        prompt.refresh_from_db()
        assert "roto" not in prompt.user_template

    def test_la_vista_previa_no_llama_al_modelo(self, api, prompt):
        with patch("apps.api.gestion.get_provider") as doble:
            respuesta = api.post(
                reverse("api-gestion-prompt-vista-previa", args=[prompt.pk]), {}, format="json"
            )
            doble.assert_not_called()

        datos = respuesta.json()
        assert respuesta.status_code == 200
        assert datos["system"]
        assert "«perfil»" in datos["mensaje"]

    def test_la_vista_previa_delata_una_variable_que_no_existe(self, api, prompt):
        api.patch(
            reverse("api-gestion-prompt-detail", args=[prompt.pk]),
            {"user_template": "Perfil: {{ perfil }}\nEdad: {{ edda }}"},
            format="json",
        )

        datos = api.post(
            reverse("api-gestion-prompt-vista-previa", args=[prompt.pk]), {}, format="json"
        ).json()

        assert datos["desconocidas"] == ["edda"]

    def test_no_se_pueden_borrar(self, api, prompt):
        respuesta = api.delete(reverse("api-gestion-prompt-detail", args=[prompt.pk]))

        assert respuesta.status_code == 405
        assert PromptTemplate.objects.filter(pk=prompt.pk).exists()


@pytest.fixture
def almacen():
    return VectorStore.objects.create(name="Libros", openai_vector_store_id="vs_123")


class TestElRag:
    def test_el_almacen_trae_el_estado_de_sus_documentos(self, api, almacen, jefa):
        for estado, cuantos in ((DocumentStatus.INDEXED, 2), (DocumentStatus.FAILED, 1)):
            for n in range(cuantos):
                KnowledgeDocument.objects.create(
                    vector_store=almacen, title=f"{estado}-{n}",
                    file=f"knowledge/{estado}-{n}.pdf", status=estado, uploaded_by=jefa,
                )

        datos = api.get(reverse("api-gestion-almacen-list")).json()[0]

        assert datos["documentos"] == {"total": 3, "indexados": 2, "fallidos": 1}
        assert datos["is_ready"] is True

    def test_crear_uno_ya_creado_se_rechaza(self, api, almacen):
        respuesta = api.post(reverse("api-gestion-almacen-crear-en-openai", args=[almacen.pk]))

        assert respuesta.status_code == 409

    def test_un_fallo_de_openai_no_es_un_500(self, api):
        nuevo = VectorStore.objects.create(name="Sin crear")
        with patch("apps.api.gestion.rag.create_vector_store") as crear:
            crear.side_effect = rag.RAGError("sin clave")
            respuesta = api.post(reverse("api-gestion-almacen-crear-en-openai", args=[nuevo.pk]))

        assert respuesta.status_code == 502
        assert respuesta.json()["detail"] == "sin clave"

    def test_reindexar_limpia_el_error_anterior(self, api, almacen, jefa):
        documento = KnowledgeDocument.objects.create(
            vector_store=almacen, title="Libro", file="knowledge/libro.pdf",
            status=DocumentStatus.FAILED, error="se agotó el tiempo", uploaded_by=jefa,
        )

        with patch("apps.api.gestion.rag.start_indexing") as indexar:
            def marcar(doc):
                doc.status = DocumentStatus.INDEXED
                doc.save(update_fields=["status"])

            indexar.side_effect = marcar
            respuesta = api.post(
                reverse("api-gestion-documento-reindexar", args=[documento.pk])
            )

        assert respuesta.status_code == 200
        documento.refresh_from_db()
        assert documento.status == DocumentStatus.INDEXED
        assert documento.error == ""

    def test_subir_un_documento_lo_guarda_y_empieza_a_indexarlo(
        self, api, almacen, jefa, settings, tmp_path
    ):
        settings.MEDIA_ROOT = tmp_path
        archivo = SimpleUploadedFile("libro.md", b"# Hipertrofia. Series y repeticiones.")

        with patch("apps.api.gestion.rag.start_indexing") as empezar:
            respuesta = api.post(
                reverse("api-gestion-documento-list"),
                {"vector_store": almacen.pk, "title": "Libro de hipertrofia", "file": archivo},
                format="multipart",
            )

        assert respuesta.status_code == 201
        documento = KnowledgeDocument.objects.get()
        assert documento.uploaded_by == jefa
        empezar.assert_called_once()

    def test_subir_no_espera_al_troceado(self, api, almacen, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        archivo = SimpleUploadedFile("libro.md", b"# Series y repeticiones.")

        with (
            patch("apps.api.gestion.rag.start_indexing"),
            patch("apps.aiassist.rag.index_document") as con_espera,
        ):
            api.post(
                reverse("api-gestion-documento-list"),
                {"vector_store": almacen.pk, "title": "Libro", "file": archivo},
                format="multipart",
            )

        con_espera.assert_not_called()

    def test_un_ejecutable_renombrado_a_pdf_no_pasa(self, api, almacen, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        archivo = SimpleUploadedFile("libro.pdf", bytes([0x4D, 0x5A, 0x90, 0x00]) * 64)

        with patch("apps.api.gestion.rag.start_indexing") as empezar:
            respuesta = api.post(
                reverse("api-gestion-documento-list"),
                {"vector_store": almacen.pk, "title": "Trampa", "file": archivo},
                format="multipart",
            )

        assert respuesta.status_code == 400
        assert "file" in respuesta.json()
        assert not KnowledgeDocument.objects.exists()
        empezar.assert_not_called()

    def test_si_openai_falla_la_subida_no_se_pierde(self, api, almacen, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        archivo = SimpleUploadedFile("guia.txt", b"Progresion de cargas.")

        def fallar(documento):
            documento.status = DocumentStatus.FAILED
            documento.error = "OpenAI no responde"
            documento.save(update_fields=["status", "error"])
            raise rag.RAGError("OpenAI no responde")

        with patch("apps.api.gestion.rag.start_indexing", side_effect=fallar):
            respuesta = api.post(
                reverse("api-gestion-documento-list"),
                {"vector_store": almacen.pk, "title": "Guía", "file": archivo},
                format="multipart",
            )

        assert respuesta.status_code == 201
        documento = KnowledgeDocument.objects.get()
        assert documento.status == DocumentStatus.FAILED
        assert "no responde" in documento.error

    def test_borrar_lo_quita_tambien_de_openai(self, api, almacen, jefa):
        documento = KnowledgeDocument.objects.create(
            vector_store=almacen, title="Libro", file="knowledge/libro.pdf",
            status=DocumentStatus.INDEXED, openai_file_id="file_123", uploaded_by=jefa,
        )

        with patch("apps.api.gestion.rag.delete_document") as borrar_remoto:
            respuesta = api.delete(
                reverse("api-gestion-documento-detail", args=[documento.pk])
            )

        assert respuesta.status_code == 204
        borrar_remoto.assert_called_once()
        assert not KnowledgeDocument.objects.exists()

    def test_si_falla_el_borrado_remoto_la_fila_se_queda(self, api, almacen, jefa):
        documento = KnowledgeDocument.objects.create(
            vector_store=almacen, title="Libro", file="knowledge/libro.pdf",
            status=DocumentStatus.INDEXED, openai_file_id="file_123", uploaded_by=jefa,
        )

        with patch(
            "apps.api.gestion.rag.delete_document",
            side_effect=rag.RAGError("OpenAI no responde"),
        ):
            respuesta = api.delete(
                reverse("api-gestion-documento-detail", args=[documento.pk])
            )

        assert respuesta.status_code == 502
        assert KnowledgeDocument.objects.filter(pk=documento.pk).exists()

    def test_los_limites_de_subida_los_dice_el_servidor(self, api):
        datos = api.get(reverse("api-gestion-documento-limites")).json()

        assert ".pdf" in datos["extensiones"]
        assert datos["max_bytes"] == settings.RAG_MAX_UPLOAD_BYTES

    def test_se_filtran_los_documentos_por_estado(self, api, almacen, jefa):
        for estado in (DocumentStatus.INDEXED, DocumentStatus.FAILED):
            KnowledgeDocument.objects.create(
                vector_store=almacen, title=str(estado), file=f"knowledge/{estado}.pdf",
                status=estado, uploaded_by=jefa,
            )

        datos = api.get(
            reverse("api-gestion-documento-list"), {"estado": DocumentStatus.FAILED}
        ).json()

        assert [d["status"] for d in datos] == [DocumentStatus.FAILED]


class TestLaProgramacion:
    def test_las_tres_filas_estan_desde_la_migracion(self, api):
        datos = api.get(reverse("api-gestion-programacion-list")).json()

        assert {fila["goal"] for fila in datos} == set(TrainingGoal.values)
        hipertrofia = next(f for f in datos if f["goal"] == TrainingGoal.HYPERTROPHY)
        assert hipertrofia["sets_min"] == 3
        assert "3-4 series" in hipertrofia["resumen"]

    def test_ajustar_un_numero_cambia_lo_que_se_valida(self, api):
        fila = ProgrammingRules.objects.get(goal=TrainingGoal.HYPERTROPHY)

        respuesta = api.patch(
            reverse("api-gestion-programacion-detail", args=[fila.pk]),
            {"sets_min": 4},
            format="json",
        )

        assert respuesta.status_code == 200
        assert programacion.reglas_de(TrainingGoal.HYPERTROPHY).sets_min == 4

    def test_un_maximo_por_debajo_del_minimo_se_rechaza_por_campo(self, api):
        fila = ProgrammingRules.objects.get(goal=TrainingGoal.HYPERTROPHY)

        respuesta = api.patch(
            reverse("api-gestion-programacion-detail", args=[fila.pk]),
            {"sets_max": 1},
            format="json",
        )

        assert respuesta.status_code == 400
        assert "sets_max" in respuesta.json()

    def test_el_objetivo_no_se_puede_cambiar(self, api):
        fila = ProgrammingRules.objects.get(goal=TrainingGoal.HYPERTROPHY)

        api.patch(
            reverse("api-gestion-programacion-detail", args=[fila.pk]),
            {"goal": TrainingGoal.STRENGTH},
            format="json",
        )

        fila.refresh_from_db()
        assert fila.goal == TrainingGoal.HYPERTROPHY

    def test_no_se_crean_ni_se_borran(self, api):
        fila = ProgrammingRules.objects.get(goal=TrainingGoal.HYPERTROPHY)

        alta = api.post(reverse("api-gestion-programacion-list"), {}, format="json")
        baja = api.delete(reverse("api-gestion-programacion-detail", args=[fila.pk]))

        assert alta.status_code == 405
        assert baja.status_code == 405


@pytest.fixture
def generaciones(socia):
    ok = AIGeneration.objects.create(
        user=socia, kind=GenerationKind.ROUTINE, provider="anthropic", model="claude-opus-5",
        prompt_rendered="Eres un entrenador. Lesiones: hombro derecho.",
        raw_response='{"name": "Empuje"}', parsed_output={"name": "Empuje"},
        input_tokens=800, output_tokens=300, latency_ms=2000,
    )
    AIGeneration.objects.create(
        user=socia, kind=GenerationKind.PROGRESS, provider="anthropic", model="claude-opus-5",
        status=GenerationStatus.ERROR, error="se cayó",
    )
    return ok


class TestLaAuditoria:
    def test_el_listado_no_lleva_el_prompt_ni_la_respuesta_cruda(self, api, generaciones):
        cuerpo = api.get(reverse("api-gestion-generacion-list")).content.decode()

        assert "hombro derecho" not in cuerpo
        assert "prompt_rendered" not in cuerpo

    def test_el_detalle_si_los_lleva_porque_es_para_lo_que_existe(self, api, generaciones):
        datos = api.get(
            reverse("api-gestion-generacion-detail", args=[generaciones.pk])
        ).json()

        assert "hombro derecho" in datos["prompt_rendered"]
        assert datos["raw_response"]

    def test_se_filtra_por_estado_y_por_usuario(self, api, generaciones):
        errores = api.get(
            reverse("api-gestion-generacion-list"), {"estado": GenerationStatus.ERROR}
        ).json()["results"]

        assert len(errores) == 1
        assert errores[0]["status"] == GenerationStatus.ERROR

        de_socia = api.get(
            reverse("api-gestion-generacion-list"), {"usuario": "soc"}
        ).json()["results"]
        assert len(de_socia) == 2

    def test_no_se_pueden_borrar(self, api, generaciones):
        respuesta = api.delete(
            reverse("api-gestion-generacion-detail", args=[generaciones.pk])
        )

        assert respuesta.status_code == 405
        assert AIGeneration.objects.count() == 2

    def test_el_resumen_cuenta_el_gasto_y_los_fallos(self, api, generaciones):
        datos = api.get(reverse("api-gestion-generacion-resumen")).json()

        assert datos["total"] == 2
        assert datos["errores"] == 1
        assert datos["tokens"] == 1100
        tipos = {fila["tipo"]: fila for fila in datos["por_tipo"]}
        assert tipos["routine"]["total"] == 1
        assert tipos["progress"]["errores"] == 1

    def test_el_resumen_no_mira_mas_alla_de_su_ventana(self, api, socia):
        vieja = AIGeneration.objects.create(
            user=socia, kind=GenerationKind.ROUTINE, provider="anthropic", model="m",
        )
        AIGeneration.objects.filter(pk=vieja.pk).update(
            created_at=timezone.now() - timedelta(days=30)
        )

        assert api.get(reverse("api-gestion-generacion-resumen")).json()["total"] == 0


class TestLosUsuarios:
    def test_no_sale_ni_un_dato_de_salud(self, api, socia):
        from apps.api.gestion_serializers import UsuarioSerializer

        socia.injuries_notes = "hernia discal"
        socia.height_cm = 172
        socia.save()

        cuerpo = api.get(reverse("api-gestion-usuario-list")).content.decode()

        for campo in UsuarioSerializer.CAMPOS_DE_SALUD:
            assert campo not in cuerpo, f"«{campo}» se está filtrando en el panel"
        assert "hernia discal" not in cuerpo

    def test_trae_cuántas_cosas_tiene_cada_cuenta(self, api, socia):
        from apps.workouts.models import Routine, WorkoutSession

        Routine.objects.create(user=socia, name="Empuje")
        WorkoutSession.objects.create(user=socia, date=timezone.localdate())

        fila = next(
            u for u in api.get(reverse("api-gestion-usuario-list")).json()
            if u["username"] == "socia"
        )

        assert fila["entrenamientos"] == 1
        assert fila["rutinas"] == 1

    def test_se_puede_desactivar_una_cuenta(self, api, socia):
        respuesta = api.patch(
            reverse("api-gestion-usuario-detail", args=[socia.pk]),
            {"is_active": False},
            format="json",
        )

        assert respuesta.status_code == 200
        socia.refresh_from_db()
        assert socia.is_active is False

    def test_no_se_puede_cambiar_el_correo_de_otra_persona(self, api, socia):
        api.patch(
            reverse("api-gestion-usuario-detail", args=[socia.pk]),
            {"email": "del-atacante@example.com"},
            format="json",
        )

        socia.refresh_from_db()
        assert socia.email != "del-atacante@example.com"

    def test_desbloquear_borra_los_intentos_fallidos(self, api, socia, settings):
        from axes.models import AccessAttempt

        AccessAttempt.objects.create(
            username="socia", ip_address="10.0.0.1", failures_since_start=5
        )

        respuesta = api.post(reverse("api-gestion-usuario-desbloquear", args=[socia.pk]))

        assert respuesta.status_code == 200
        assert not AccessAttempt.objects.filter(username="socia").exists()

    def test_el_listado_dice_quién_está_bloqueado(self, api, socia):
        from axes.models import AccessAttempt

        AccessAttempt.objects.create(
            username="socia", ip_address="10.0.0.1", failures_since_start=5
        )

        fila = next(
            u for u in api.get(reverse("api-gestion-usuario-list")).json()
            if u["username"] == "socia"
        )

        assert fila["bloqueado"] is True

    def test_no_se_borran_cuentas_desde_el_panel(self, api, socia):
        respuesta = api.delete(reverse("api-gestion-usuario-detail", args=[socia.pk]))

        assert respuesta.status_code == 405
        assert User.objects.filter(pk=socia.pk).exists()


class TestElCatalogo:
    def test_dice_cuantos_ejercicios_hay_y_como_se_reparten(self, api):
        musculo = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
        for n in range(3):
            Exercise.objects.create(
                external_id=f"000{n}", name=f"Ej {n}", slug=f"ej-{n}", body_part="chest",
                equipment="barbell", target_muscle=musculo, is_global=True,
            )

        datos = api.get(reverse("api-gestion-catalogo")).json()

        assert datos["total"] == 3
        assert datos["por_zona"][0] == {"valor": "chest", "etiqueta": "Pecho", "n": 3}

    def test_los_ejercicios_propios_van_aparte(self, api, socia):
        musculo = MuscleGroup.objects.create(slug="abs", name="Abdominales")
        Exercise.objects.create(
            external_id="", name="Mi invento", slug="mi-invento", body_part="waist",
            equipment="body weight", target_muscle=musculo, is_global=False, created_by=socia,
        )

        datos = api.get(reverse("api-gestion-catalogo")).json()

        assert datos["total"] == 0
        assert datos["propios"] == 1


class TestLasMetricas:
    @pytest.fixture(autouse=True)
    def _catalogo(self):
        call_command("sync_metrics")

    def test_se_puede_apagar_una_metrica_para_todo_el_mundo(self, api):
        metrica = Metric.objects.first()

        api.patch(
            reverse("api-gestion-metrica-detail", args=[metrica.pk]),
            {"is_active": False},
            format="json",
        )

        metrica.refresh_from_db()
        assert metrica.is_active is False

    def test_dice_en_cuantos_paneles_esta(self, api, socia):
        metrica = Metric.objects.first()
        UserMetricPreference.objects.create(user=socia, metric=metrica, is_visible=True)

        fila = next(
            m for m in api.get(reverse("api-gestion-metrica-list")).json()
            if m["key"] == metrica.key
        )

        assert fila["en_paneles"] == 1

    def test_no_se_edita_lo_que_genera_sync_metrics(self, api):
        metrica = Metric.objects.first()

        api.patch(
            reverse("api-gestion-metrica-detail", args=[metrica.pk]),
            {"label": "Otro nombre", "key": "otra-clave"},
            format="json",
        )

        metrica.refresh_from_db()
        assert metrica.label != "Otro nombre"
        assert metrica.key != "otra-clave"

    def test_no_se_añaden_ni_se_borran(self, api):
        assert api.post(
            reverse("api-gestion-metrica-list"), {"key": "inventada"}, format="json"
        ).status_code == 405


class TestElResumenDelPanel:
    def test_avisa_de_que_no_hay_proveedor(self, api):
        assert api.get(reverse("api-gestion-resumen")).json()["proveedor"] is None

    def test_dice_si_la_clave_se_puede_descifrar(self, api, proveedor, settings):
        datos = api.get(reverse("api-gestion-resumen")).json()
        assert datos["proveedor"]["clave_usable"] is True

        settings.FIELD_ENCRYPTION_KEYS = [Fernet.generate_key().decode()]
        datos = api.get(reverse("api-gestion-resumen")).json()
        assert datos["proveedor"]["clave_usable"] is False

    def test_cuenta_lo_que_hay_que_mirar_hoy(self, api, socia, almacen, jefa):
        KnowledgeDocument.objects.create(
            vector_store=almacen, title="Roto", file="knowledge/roto.pdf",
            status=DocumentStatus.FAILED, uploaded_by=jefa,
        )
        AIGeneration.objects.create(
            user=socia, kind=GenerationKind.ROUTINE, provider="anthropic", model="m",
            status=GenerationStatus.ERROR, error="se cayó",
        )

        datos = api.get(reverse("api-gestion-resumen")).json()

        assert datos["documentos"]["fallidos"] == 1
        assert datos["generaciones"]["errores"] == 1
        assert datos["usuarios"]["total"] == 2
        assert datos["usuarios"]["nuevos"] == 2

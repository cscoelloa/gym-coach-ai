from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.aiassist.models import (
    AIProviderConfig,
    DocumentStatus,
    KnowledgeDocument,
    Provider,
    VectorStore,
)
from apps.aiassist.rag import (
    RAGError,
    create_vector_store,
    delete_document,
    get_openai_client,
    index_document,
    refresh_status,
    search,
    start_indexing,
)

pytestmark = pytest.mark.django_db

CLAVE = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def clave_de_cifrado(settings):
    settings.FIELD_ENCRYPTION_KEYS = [CLAVE]


@pytest.fixture
def config_openai():
    return AIProviderConfig.objects.create(
        provider=Provider.OPENAI,
        model="algun-modelo",
        api_key="sk-openai-de-prueba",
        is_active=True,
    )


@pytest.fixture
def store():
    return VectorStore.objects.create(name="Hipertrofia")


@pytest.fixture
def documento(store):
    return KnowledgeDocument.objects.create(
        vector_store=store,
        title="Principios de hipertrofia",
        file=SimpleUploadedFile("libro.pdf", b"%PDF-1.4\ncontenido"),
    )


class TestClienteDeOpenAI:
    def test_sin_configuracion_de_openai_lo_dice_claro(self):
        with pytest.raises(RAGError, match="necesita una configuración de OpenAI"):
            get_openai_client()

    def test_usa_la_configuracion_de_openai_aunque_no_este_activa(self):
        AIProviderConfig.objects.create(
            provider=Provider.OPENAI, model="m", api_key="sk-openai", is_active=False
        )
        AIProviderConfig.objects.create(
            provider=Provider.ANTHROPIC, api_key="sk-ant", is_active=True
        )

        with patch("openai.OpenAI") as cliente:
            get_openai_client()

        assert cliente.call_args.kwargs["api_key"] == "sk-openai"

    def test_se_niega_si_la_clave_no_se_puede_descifrar(self, config_openai, settings):
        settings.FIELD_ENCRYPTION_KEYS = [Fernet.generate_key().decode()]

        with pytest.raises(RAGError, match="no se puede descifrar"):
            get_openai_client()


class TestCrearAlmacen:
    @patch("openai.OpenAI")
    def test_guarda_el_id_devuelto(self, cliente, config_openai, store):
        cliente.return_value.vector_stores.create.return_value = MagicMock(id="vs_abc123")

        devuelto = create_vector_store(store)

        store.refresh_from_db()
        assert devuelto == "vs_abc123"
        assert store.openai_vector_store_id == "vs_abc123"
        assert store.is_ready

    @patch("openai.OpenAI")
    def test_es_idempotente(self, cliente, config_openai, store):
        store.openai_vector_store_id = "vs_ya_existe"
        store.save()

        assert create_vector_store(store) == "vs_ya_existe"
        cliente.return_value.vector_stores.create.assert_not_called()


class TestIndexarDocumento:
    def _remoto(self, status="completed"):
        remoto = MagicMock()
        remoto.id = "file_abc123"
        remoto.status = status
        remoto.last_error = None
        return remoto

    @patch("openai.OpenAI")
    def test_camino_feliz(self, cliente, config_openai, documento):
        cliente.return_value.vector_stores.create.return_value = MagicMock(id="vs_1")
        cliente.return_value.vector_stores.files.upload_and_poll.return_value = self._remoto()

        index_document(documento)

        documento.refresh_from_db()
        assert documento.status == DocumentStatus.INDEXED
        assert documento.openai_file_id == "file_abc123"
        assert documento.error == ""

    @patch("openai.OpenAI")
    def test_crea_el_almacen_si_hace_falta(self, cliente, config_openai, documento):
        cliente.return_value.vector_stores.create.return_value = MagicMock(id="vs_nuevo")
        cliente.return_value.vector_stores.files.upload_and_poll.return_value = self._remoto()

        index_document(documento)

        documento.vector_store.refresh_from_db()
        assert documento.vector_store.openai_vector_store_id == "vs_nuevo"

    @patch("openai.OpenAI")
    def test_manda_el_titulo_como_atributo_para_filtrar(self, cliente, config_openai, documento):
        cliente.return_value.vector_stores.create.return_value = MagicMock(id="vs_1")
        cliente.return_value.vector_stores.files.upload_and_poll.return_value = self._remoto()

        index_document(documento)

        atributos = cliente.return_value.vector_stores.files.upload_and_poll.call_args.kwargs[
            "attributes"
        ]
        assert atributos["title"] == "Principios de hipertrofia"

    @patch("openai.OpenAI")
    def test_respeta_el_limite_de_dieciseis_atributos(self, cliente, config_openai, documento):
        documento.attributes = {f"clave{i}": f"valor{i}" for i in range(30)}
        documento.save()
        cliente.return_value.vector_stores.create.return_value = MagicMock(id="vs_1")
        cliente.return_value.vector_stores.files.upload_and_poll.return_value = self._remoto()

        index_document(documento)

        atributos = cliente.return_value.vector_stores.files.upload_and_poll.call_args.kwargs[
            "attributes"
        ]
        assert len(atributos) <= 16

    @patch("openai.OpenAI")
    def test_un_fallo_de_openai_deja_el_motivo_guardado(self, cliente, config_openai, documento):
        remoto = self._remoto(status="failed")
        remoto.last_error = MagicMock(message="El archivo no se pudo procesar")
        cliente.return_value.vector_stores.create.return_value = MagicMock(id="vs_1")
        cliente.return_value.vector_stores.files.upload_and_poll.return_value = remoto

        with pytest.raises(RAGError):
            index_document(documento)

        documento.refresh_from_db()
        assert documento.status == DocumentStatus.FAILED
        assert "no se pudo procesar" in documento.error

    @patch("openai.OpenAI")
    def test_una_excepcion_del_sdk_queda_registrada(self, cliente, config_openai, documento):
        import openai

        cliente.return_value.vector_stores.create.return_value = MagicMock(id="vs_1")
        cliente.return_value.vector_stores.files.upload_and_poll.side_effect = openai.APIError(
            "límite de tasa", request=MagicMock(), body=None
        )

        with pytest.raises(RAGError):
            index_document(documento)

        documento.refresh_from_db()
        assert documento.status == DocumentStatus.FAILED
        assert documento.error


class TestBusqueda:
    @patch("openai.OpenAI")
    def test_ordena_por_puntuacion_entre_almacenes(self, cliente, config_openai):
        def resultado(score, texto):
            item = MagicMock()
            item.score = score
            item.filename = "libro.pdf"
            item.attributes = {}
            parte = MagicMock()
            parte.type = "text"
            parte.text = texto
            item.content = [parte]
            return item

        cliente.return_value.vector_stores.search.side_effect = [
            MagicMock(data=[resultado(0.4, "flojo")]),
            MagicMock(data=[resultado(0.9, "bueno")]),
        ]

        resultados = search("volumen", ["vs_1", "vs_2"])

        assert [r["text"] for r in resultados] == ["bueno", "flojo"]

    def test_sin_almacenes_no_llama_a_nadie(self, config_openai):
        assert search("lo que sea", []) == []


class TestBorrarDocumento:
    @patch("openai.OpenAI")
    def test_lo_saca_del_almacen_y_borra_el_archivo(self, cliente, config_openai, documento):
        documento.vector_store.openai_vector_store_id = "vs_abc"
        documento.vector_store.save()
        documento.openai_file_id = "file_123"
        documento.save()

        delete_document(documento)

        cliente.return_value.vector_stores.files.delete.assert_called_once_with(
            "file_123", vector_store_id="vs_abc"
        )
        cliente.return_value.files.delete.assert_called_once_with("file_123")

    @patch("openai.OpenAI")
    def test_sin_archivo_remoto_no_llama_a_nadie(self, cliente, config_openai, documento):
        delete_document(documento)

        cliente.assert_not_called()

    @patch("openai.OpenAI")
    def test_si_ya_no_estaba_alli_no_es_un_fallo(self, cliente, config_openai, documento):
        import httpx
        import openai

        documento.openai_file_id = "file_123"
        documento.save()
        cliente.return_value.vector_stores.files.delete.side_effect = openai.NotFoundError(
            "no está",
            response=httpx.Response(404, request=httpx.Request("DELETE", "https://api.openai.com")),
            body=None,
        )

        delete_document(documento)


class TestEmpezarAIndexar:
    @patch("openai.OpenAI")
    def test_sube_adjunta_y_deja_el_documento_indexandose(self, cliente, config_openai, documento):
        documento.vector_store.openai_vector_store_id = "vs_1"
        documento.vector_store.save()
        cliente.return_value.files.create.return_value = MagicMock(id="file_nuevo")

        start_indexing(documento)

        documento.refresh_from_db()
        assert documento.status == DocumentStatus.INDEXING
        assert documento.openai_file_id == "file_nuevo"
        cliente.return_value.vector_stores.files.upload_and_poll.assert_not_called()

    @patch("openai.OpenAI")
    def test_manda_el_titulo_como_atributo(self, cliente, config_openai, documento):
        documento.vector_store.openai_vector_store_id = "vs_1"
        documento.vector_store.save()
        cliente.return_value.files.create.return_value = MagicMock(id="file_nuevo")

        start_indexing(documento)

        atributos = cliente.return_value.vector_stores.files.create.call_args.kwargs["attributes"]
        assert atributos["title"] == "Principios de hipertrofia"

    @patch("openai.OpenAI")
    def test_un_fallo_deja_el_motivo_guardado(self, cliente, config_openai, documento):
        import openai

        documento.vector_store.openai_vector_store_id = "vs_1"
        documento.vector_store.save()
        cliente.return_value.files.create.side_effect = openai.APIError(
            "clave inválida", request=MagicMock(), body=None
        )

        with pytest.raises(RAGError):
            start_indexing(documento)

        documento.refresh_from_db()
        assert documento.status == DocumentStatus.FAILED
        assert documento.error


class TestConsultarEstado:
    def _remoto(self, status, mensaje=""):
        remoto = MagicMock()
        remoto.status = status
        remoto.last_error = MagicMock(message=mensaje) if mensaje else None
        return remoto

    @pytest.fixture
    def indexandose(self, documento):
        documento.vector_store.openai_vector_store_id = "vs_1"
        documento.vector_store.save()
        documento.status = DocumentStatus.INDEXING
        documento.openai_file_id = "file_1"
        documento.save()
        return documento

    @patch("openai.OpenAI")
    def test_completado_pasa_a_indexado(self, cliente, config_openai, indexandose):
        cliente.return_value.vector_stores.files.retrieve.return_value = self._remoto("completed")

        assert refresh_status(indexandose) == DocumentStatus.INDEXED

    @patch("openai.OpenAI")
    def test_fallido_guarda_el_motivo(self, cliente, config_openai, indexandose):
        cliente.return_value.vector_stores.files.retrieve.return_value = self._remoto(
            "failed", "no se pudo leer el PDF"
        )

        assert refresh_status(indexandose) == DocumentStatus.FAILED
        indexandose.refresh_from_db()
        assert "no se pudo leer" in indexandose.error

    @patch("openai.OpenAI")
    def test_en_curso_lo_deja_como_estaba(self, cliente, config_openai, indexandose):
        cliente.return_value.vector_stores.files.retrieve.return_value = self._remoto(
            "in_progress"
        )

        assert refresh_status(indexandose) == DocumentStatus.INDEXING

    @patch("openai.OpenAI")
    def test_no_pregunta_por_los_que_ya_tienen_estado_final(
        self, cliente, config_openai, documento
    ):
        documento.status = DocumentStatus.INDEXED
        documento.save()

        assert refresh_status(documento) == DocumentStatus.INDEXED
        cliente.assert_not_called()

    @patch("openai.OpenAI")
    def test_si_no_se_puede_preguntar_no_cambia_el_estado(
        self, cliente, config_openai, indexandose
    ):
        import openai

        cliente.return_value.vector_stores.files.retrieve.side_effect = openai.APIError(
            "timeout", request=MagicMock(), body=None
        )

        assert refresh_status(indexandose) == DocumentStatus.INDEXING

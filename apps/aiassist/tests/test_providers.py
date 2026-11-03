from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from apps.aiassist.models import AIProviderConfig, Provider
from apps.aiassist.providers import ProviderError, ProviderRefusal, get_provider
from apps.aiassist.providers.anthropic_provider import AnthropicProvider
from apps.aiassist.providers.google_provider import GoogleProvider
from apps.aiassist.providers.openai_provider import MAX_FRAGMENTOS_RAG, OpenAIProvider
from apps.aiassist.schemas import ConnectionTest

pytestmark = pytest.mark.django_db

CLAVE = Fernet.generate_key().decode()
ESPERADO = ConnectionTest(ok=True, message="hola")


@pytest.fixture(autouse=True)
def clave_de_cifrado(settings):
    settings.FIELD_ENCRYPTION_KEYS = [CLAVE]


def config(provider, **kwargs):
    return AIProviderConfig.objects.create(
        provider=provider, api_key="clave-de-prueba-1234", **kwargs
    )


class TestAnthropic:
    def _respuesta(self, stop_reason="end_turn"):
        respuesta = MagicMock()
        respuesta.parsed_output = ESPERADO
        respuesta.stop_reason = stop_reason
        respuesta.usage.input_tokens = 100
        respuesta.usage.output_tokens = 20
        bloque = MagicMock()
        bloque.type = "text"
        bloque.text = '{"ok": true}'
        respuesta.content = [bloque]
        return respuesta

    @patch("anthropic.Anthropic")
    def test_construye_la_peticion_correcta(self, cliente):
        cliente.return_value.messages.parse.return_value = self._respuesta()
        provider = AnthropicProvider(config(Provider.ANTHROPIC))

        provider.generate_structured(system="sistema", user="usuario", schema=ConnectionTest)

        kwargs = cliente.return_value.messages.parse.call_args.kwargs
        assert kwargs["model"] == "claude-opus-5"
        assert kwargs["output_format"] is ConnectionTest
        assert kwargs["thinking"] == {"type": "adaptive"}
        assert kwargs["messages"] == [{"role": "user", "content": "usuario"}]

    @patch("anthropic.Anthropic")
    def test_no_envia_parametros_que_este_modelo_rechaza(self, cliente):
        cliente.return_value.messages.parse.return_value = self._respuesta()
        provider = AnthropicProvider(config(Provider.ANTHROPIC))

        provider.generate_structured(system="s", user="u", schema=ConnectionTest)

        kwargs = cliente.return_value.messages.parse.call_args.kwargs
        assert "temperature" not in kwargs
        assert "top_p" not in kwargs
        assert "budget_tokens" not in kwargs.get("thinking", {})

    @patch("anthropic.Anthropic")
    def test_el_esfuerzo_solo_se_envia_si_esta_configurado(self, cliente):
        cliente.return_value.messages.parse.return_value = self._respuesta()

        AnthropicProvider(config(Provider.ANTHROPIC)).generate_structured(
            system="s", user="u", schema=ConnectionTest
        )
        assert "output_config" not in cliente.return_value.messages.parse.call_args.kwargs

        AIProviderConfig.objects.all().delete()
        AnthropicProvider(config(Provider.ANTHROPIC, effort="high")).generate_structured(
            system="s", user="u", schema=ConnectionTest
        )
        kwargs = cliente.return_value.messages.parse.call_args.kwargs
        assert kwargs["output_config"] == {"effort": "high"}

    @patch("anthropic.Anthropic")
    def test_un_rechazo_no_se_confunde_con_una_respuesta(self, cliente):
        respuesta = self._respuesta(stop_reason="refusal")
        respuesta.content = []
        cliente.return_value.messages.parse.return_value = respuesta

        with pytest.raises(ProviderRefusal):
            AnthropicProvider(config(Provider.ANTHROPIC)).generate_structured(
                system="s", user="u", schema=ConnectionTest
            )

    @patch("anthropic.Anthropic")
    def test_avisa_si_la_respuesta_se_corto(self, cliente):
        cliente.return_value.messages.parse.return_value = self._respuesta(stop_reason="max_tokens")

        resultado = AnthropicProvider(config(Provider.ANTHROPIC)).generate_structured(
            system="s", user="u", schema=ConnectionTest
        )

        assert any("max_tokens" in nota for nota in resultado.notes)

    @patch("anthropic.Anthropic")
    def test_traduce_la_salida(self, cliente):
        cliente.return_value.messages.parse.return_value = self._respuesta()

        resultado = AnthropicProvider(config(Provider.ANTHROPIC)).generate_structured(
            system="s", user="u", schema=ConnectionTest
        )

        assert resultado.parsed == ESPERADO
        assert resultado.input_tokens == 100
        assert resultado.output_tokens == 20

    def test_no_soporta_rag(self):
        assert AnthropicProvider.supports_rag is False


class TestOpenAI:
    def _respuesta(self, parsed=ESPERADO, status="completed"):
        respuesta = MagicMock()
        respuesta.output_parsed = parsed
        respuesta.status = status
        respuesta.output_text = '{"ok": true}'
        respuesta.usage.input_tokens = 200
        respuesta.usage.output_tokens = 30
        return respuesta

    @patch("openai.OpenAI")
    def test_sin_almacenes_no_manda_herramientas(self, cliente):
        cliente.return_value.responses.parse.return_value = self._respuesta()

        OpenAIProvider(config(Provider.OPENAI, model="algun-modelo")).generate_structured(
            system="s", user="u", schema=ConnectionTest
        )

        assert "tools" not in cliente.return_value.responses.parse.call_args.kwargs

    @patch("openai.OpenAI")
    def test_con_almacenes_activa_file_search(self, cliente):
        cliente.return_value.responses.parse.return_value = self._respuesta()

        OpenAIProvider(config(Provider.OPENAI, model="algun-modelo")).generate_structured(
            system="s", user="u", schema=ConnectionTest, vector_store_ids=["vs_1", "vs_2"]
        )

        herramientas = cliente.return_value.responses.parse.call_args.kwargs["tools"]
        assert herramientas == [
            {
                "type": "file_search",
                "vector_store_ids": ["vs_1", "vs_2"],
                "max_num_results": MAX_FRAGMENTOS_RAG,
            }
        ]

    @patch("openai.OpenAI")
    def test_una_respuesta_incompleta_es_un_error(self, cliente):
        respuesta = self._respuesta(status="incomplete")
        respuesta.incomplete_details.reason = "max_output_tokens"
        cliente.return_value.responses.parse.return_value = respuesta

        with pytest.raises(ProviderError, match="incompleta"):
            OpenAIProvider(config(Provider.OPENAI, model="m")).generate_structured(
                system="s", user="u", schema=ConnectionTest
            )

    @patch("openai.OpenAI")
    def test_sin_salida_parseada_es_un_rechazo(self, cliente):
        cliente.return_value.responses.parse.return_value = self._respuesta(parsed=None)

        with pytest.raises(ProviderRefusal):
            OpenAIProvider(config(Provider.OPENAI, model="m")).generate_structured(
                system="s", user="u", schema=ConnectionTest
            )

    def test_soporta_rag(self):
        assert OpenAIProvider.supports_rag is True


class TestGoogle:
    def _respuesta(self, parsed=ESPERADO):
        respuesta = MagicMock()
        respuesta.parsed = parsed
        respuesta.text = '{"ok": true}'
        respuesta.usage_metadata.prompt_token_count = 300
        respuesta.usage_metadata.candidates_token_count = 40
        return respuesta

    @patch("google.genai.Client")
    def test_pide_json_con_esquema(self, cliente):
        cliente.return_value.models.generate_content.return_value = self._respuesta()

        GoogleProvider(config(Provider.GOOGLE, model="algun-modelo")).generate_structured(
            system="sistema", user="usuario", schema=ConnectionTest
        )

        kwargs = cliente.return_value.models.generate_content.call_args.kwargs
        assert kwargs["config"].response_mime_type == "application/json"
        assert kwargs["config"].response_schema is ConnectionTest
        assert kwargs["config"].system_instruction == "sistema"

    @patch("google.genai.Client")
    def test_traduce_el_recuento_de_tokens(self, cliente):
        cliente.return_value.models.generate_content.return_value = self._respuesta()

        resultado = GoogleProvider(config(Provider.GOOGLE, model="m")).generate_structured(
            system="s", user="u", schema=ConnectionTest
        )

        assert resultado.input_tokens == 300
        assert resultado.output_tokens == 40

    @patch("google.genai.Client")
    def test_sin_salida_parseada_es_un_rechazo(self, cliente):
        cliente.return_value.models.generate_content.return_value = self._respuesta(parsed=None)

        with pytest.raises(ProviderRefusal):
            GoogleProvider(config(Provider.GOOGLE, model="m")).generate_structured(
                system="s", user="u", schema=ConnectionTest
            )

    def test_no_soporta_rag(self):
        assert GoogleProvider.supports_rag is False


class TestFactoria:
    def test_devuelve_el_adaptador_de_la_configuracion_activa(self):
        config(Provider.ANTHROPIC, is_active=True)

        assert isinstance(get_provider(), AnthropicProvider)

    def test_sin_configuracion_activa_lo_dice_claro(self):
        with pytest.raises(ProviderError, match="No hay ninguna configuración"):
            get_provider()

    def test_cada_proveedor_tiene_su_adaptador(self):
        casos = [
            (Provider.ANTHROPIC, AnthropicProvider),
            (Provider.OPENAI, OpenAIProvider),
            (Provider.GOOGLE, GoogleProvider),
        ]
        for provider, clase in casos:
            AIProviderConfig.objects.all().delete()
            assert isinstance(get_provider(config(provider, model="m", is_active=True)), clase)

    def test_solo_anthropic_tiene_modelo_por_defecto(self):
        assert AnthropicProvider(config(Provider.ANTHROPIC)).model == "claude-opus-5"

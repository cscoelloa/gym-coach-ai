from ..models import AIProviderConfig, Provider
from .anthropic_provider import AnthropicProvider
from .base import LLMProvider, ProviderError
from .google_provider import GoogleProvider
from .openai_provider import OpenAIProvider

PROVIDERS: dict[str, type[LLMProvider]] = {
    Provider.ANTHROPIC: AnthropicProvider,
    Provider.OPENAI: OpenAIProvider,
    Provider.GOOGLE: GoogleProvider,
}


def get_provider(config: AIProviderConfig | None = None) -> LLMProvider:
    if config is None:
        config = AIProviderConfig.objects.filter(is_active=True).first()

    if config is None:
        raise ProviderError(
            "No hay ninguna configuración de IA activa. Créala en /admin/ → Configuraciones de IA."
        )

    provider_class = PROVIDERS.get(config.provider)
    if provider_class is None:
        raise ProviderError(f"Proveedor desconocido: «{config.provider}».")

    if not config.has_usable_key:
        raise ProviderError(
            f"La API key de «{config}» no se puede descifrar con las claves actuales de "
            "FIELD_ENCRYPTION_KEYS. Vuelve a pegarla en /admin/ o restaura la clave de cifrado. "
            "Ver .docs/05-runbook.md"
        )

    return provider_class(config)


def active_vector_store_ids() -> list[str]:
    from ..models import VectorStore

    return list(
        VectorStore.objects.filter(is_active=True)
        .exclude(openai_vector_store_id="")
        .values_list("openai_vector_store_id", flat=True)
    )

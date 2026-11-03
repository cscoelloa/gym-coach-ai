import time

import anthropic
from pydantic import BaseModel

from .base import LLMProvider, ProviderError, ProviderRefusal, ProviderResult


class AnthropicProvider(LLMProvider):
    supports_rag = False
    default_model = "claude-opus-5"

    def generate_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        vector_store_ids: list[str] | None = None,
    ) -> ProviderResult:
        client = anthropic.Anthropic(
            api_key=self.config.api_key,
            timeout=float(self.config.timeout_seconds),
        )

        kwargs = {
            "model": self.model,
            "max_tokens": self.config.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_format": schema,
            "thinking": {"type": "adaptive"},
        }
        if self.config.effort:
            kwargs["output_config"] = {"effort": self.config.effort}

        started = time.perf_counter()
        try:
            response = client.messages.parse(**kwargs)
        except anthropic.APIError as exc:
            raise ProviderError(f"Anthropic: {exc}") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        if response.stop_reason == "refusal":
            detail = getattr(response.stop_details, "explanation", "") or ""
            raise ProviderRefusal(f"El modelo rechazó la petición. {detail}".strip())

        notes = []
        if response.stop_reason == "max_tokens":
            notes.append(
                "La respuesta se cortó por el límite de tokens; sube `max_tokens` en la "
                "configuración."
            )

        return ProviderResult(
            parsed=response.parsed_output,
            raw_text=_first_text(response),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=latency_ms,
            notes=notes,
        )


def _first_text(response) -> str:
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""

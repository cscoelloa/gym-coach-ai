import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from .base import LLMProvider, ProviderError, ProviderRefusal, ProviderResult


class GoogleProvider(LLMProvider):
    supports_rag = False

    def generate_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        vector_store_ids: list[str] | None = None,
    ) -> ProviderResult:
        client = genai.Client(
            api_key=self.config.api_key,
            http_options=types.HttpOptions(timeout=self.config.timeout_seconds * 1000),
        )

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
            max_output_tokens=self.config.max_tokens,
        )

        started = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=self.model, contents=user, config=config
            )
        except genai_errors.APIError as exc:
            raise ProviderError(f"Google: {exc}") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        parsed = response.parsed
        if parsed is None:
            raise ProviderRefusal("Google no devolvió una respuesta que encaje en el esquema.")

        usage = response.usage_metadata
        return ProviderResult(
            parsed=parsed,
            raw_text=response.text or "",
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0 if usage else 0,
            output_tokens=getattr(usage, "candidates_token_count", 0) or 0 if usage else 0,
            latency_ms=latency_ms,
        )

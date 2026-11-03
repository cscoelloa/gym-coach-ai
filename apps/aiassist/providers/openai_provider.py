import time

import openai
from pydantic import BaseModel

from .base import LLMProvider, ProviderError, ProviderRefusal, ProviderResult

MAX_FRAGMENTOS_RAG = 3

MAX_REINTENTOS = 5


class OpenAIProvider(LLMProvider):
    supports_rag = True

    def generate_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        vector_store_ids: list[str] | None = None,
    ) -> ProviderResult:
        client = openai.OpenAI(
            api_key=self.config.api_key,
            timeout=float(self.config.timeout_seconds),
            max_retries=MAX_REINTENTOS,
        )

        kwargs = {
            "model": self.model,
            "instructions": system,
            "input": user,
            "text_format": schema,
            "max_output_tokens": self.config.max_tokens,
        }
        if vector_store_ids:
            kwargs["tools"] = [
                {
                    "type": "file_search",
                    "vector_store_ids": list(vector_store_ids),
                    "max_num_results": MAX_FRAGMENTOS_RAG,
                }
            ]

        started = time.perf_counter()
        try:
            response = client.responses.parse(**kwargs)
        except openai.APIError as exc:
            raise ProviderError(f"OpenAI: {exc}") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        if response.status == "incomplete":
            reason = getattr(response.incomplete_details, "reason", "") or "desconocida"
            raise ProviderError(f"OpenAI devolvió una respuesta incompleta ({reason}).")

        parsed = response.output_parsed
        if parsed is None:
            raise ProviderRefusal("OpenAI no devolvió una respuesta que encaje en el esquema.")

        usage = response.usage
        return ProviderResult(
            parsed=parsed,
            raw_text=getattr(response, "output_text", "") or "",
            input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
            latency_ms=latency_ms,
        )

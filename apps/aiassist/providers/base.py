from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel


class ProviderError(Exception):
    pass


class ProviderRefusal(ProviderError):
    pass


@dataclass
class ProviderResult:
    parsed: BaseModel
    raw_text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    notes: list[str] = field(default_factory=list)


class LLMProvider(ABC):
    supports_rag: bool = False
    default_model: str = ""

    def __init__(self, config):
        self.config = config

    @property
    def model(self) -> str:
        return self.config.model or self.default_model

    @abstractmethod
    def generate_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        vector_store_ids: list[str] | None = None,
    ) -> ProviderResult:
        pass

    def retrieve_context(self, query: str, vector_store_ids: list[str]) -> list[str]:
        return []

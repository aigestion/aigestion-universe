"""Common provider interface."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProviderKind(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"


@dataclass
class ProviderResponse:
    text: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0  # raw provider cost; gateway applies zero markup
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class Provider:
    """Protocol every BYOK adapter must satisfy."""

    kind: ProviderKind
    name: str

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any) -> None:
        self.api_key = api_key

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def complete(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        raise NotImplementedError

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Return USD cost using published per-token pricing (zero markup)."""
        return 0.0

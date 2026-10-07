"""OpenAI provider adapter (BYOK)."""
from __future__ import annotations

from typing import Any, Dict, Optional
import httpx

from .base import Provider, ProviderKind, ProviderResponse

# Per-1k-token pricing (USD) — zero markup applied on top.
PRICING: Dict[str, tuple[float, float]] = {
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-3.5-turbo": (0.0005, 0.0015),
}
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(Provider):
    kind = ProviderKind.OPENAI
    name = "openai"

    async def complete(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        model = model or DEFAULT_MODEL
        messages: list[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        return ProviderResponse(
            text=choice["message"]["content"],
            provider=self.name,
            model=model,
            prompt_tokens=pt,
            completion_tokens=ct,
            cost_usd=self.estimate_cost(model, pt, ct),
            raw=data,
        )

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        in_cost, out_cost = PRICING.get(model, PRICING[DEFAULT_MODEL])
        return (prompt_tokens / 1000) * in_cost + (completion_tokens / 1000) * out_cost

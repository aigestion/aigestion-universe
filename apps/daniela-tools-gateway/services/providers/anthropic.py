"""Anthropic provider adapter (BYOK)."""
from __future__ import annotations

from typing import Any, Dict, Optional
import httpx

from .base import Provider, ProviderKind, ProviderResponse

# Per-1k-token pricing (USD) — zero markup.
PRICING: Dict[str, tuple[float, float]] = {
    "claude-3-5-sonnet-20241022": (0.003, 0.015),
    "claude-3-5-haiku-20241022": (0.0008, 0.004),
    "claude-3-opus-20240229": (0.015, 0.075),
    "claude-3-sonnet-20240229": (0.003, 0.015),
    "claude-3-haiku-20240307": (0.00025, 0.00125),
}
DEFAULT_MODEL = "claude-3-5-haiku-20241022"


class AnthropicProvider(Provider):
    kind = ProviderKind.ANTHROPIC
    name = "anthropic"

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
        headers = {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        text = "".join(
            block.get("text", "") for block in data.get("content", [])
        )
        usage = data.get("usage", {})
        pt = usage.get("input_tokens", 0)
        ct = usage.get("output_tokens", 0)
        return ProviderResponse(
            text=text,
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

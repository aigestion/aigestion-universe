"""Google (Gemini) provider adapter (BYOK)."""
from __future__ import annotations

from typing import Any, Dict, Optional
import httpx

from .base import Provider, ProviderKind, ProviderResponse

# Per-1k-token pricing (USD) — zero markup.
PRICING: Dict[str, tuple[float, float]] = {
    "gemini-1.5-flash": (0.000075, 0.0003),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-2.0-flash": (0.0001, 0.0004),
}
DEFAULT_MODEL = "gemini-1.5-flash"


class GoogleProvider(Provider):
    kind = ProviderKind.GOOGLE
    name = "google"

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
        parts: list[Dict[str, str]] = []
        if system:
            parts.append({"text": system})
        parts.append({"text": prompt})

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params = {"key": self.api_key or ""}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, params=params, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            for part in candidates[0].get("content", {}).get("parts", []):
                text += part.get("text", "")

        usage = data.get("usageMetadata", {})
        pt = usage.get("promptTokenCount", 0)
        ct = usage.get("candidatesTokenCount", 0)
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

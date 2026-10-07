"""Local LLM provider adapter (e.g. llama.cpp OpenAI-compatible server).

Zero cost — runs on your own hardware. BYOK not required.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
import httpx

from .base import Provider, ProviderKind, ProviderResponse

DEFAULT_URL = os.environ.get("LOCAL_LLM_URL", "http://localhost:8080/v1")
DEFAULT_MODEL = "local-model"


class LocalProvider(Provider):
    kind = ProviderKind.LOCAL
    name = "local"

    def __init__(self, api_key: Optional[str] = None, base_url: str = DEFAULT_URL, **kwargs: Any) -> None:
        super().__init__(api_key, **kwargs)
        self.base_url = base_url

    @property
    def configured(self) -> bool:
        # Local server is "configured" if reachable; no key needed.
        return True

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

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload)
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
            cost_usd=0.0,  # local = free
            raw=data,
        )

"""Answer generators.

The retrieval stack is complete without a language model, so this module is
optional. A generator is any callable ``(query, sources) -> str``; composing
answers without one falls back to the extractive path in ``generation.py``.

Two implementations are provided:

``OpenRouterGenerator``
    Calls a chat-completions model over HTTPS using only the standard library,
    so no SDK is added to the dependency list. Activated by the presence of
    ``OPENROUTER_API_KEY``.

``generator_from_env``
    Factory that reads the environment and returns a generator, or ``None`` when
    none is configured, so callers never need to branch on availability.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Sequence

__all__ = [
    "OpenRouterGenerator",
    "GeneratorError",
    "generator_from_env",
    "build_context_prompt",
]

DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-sonnet-5.5"
DEFAULT_TIMEOUT = 60.0


class GeneratorError(RuntimeError):
    """Raised when the generator cannot produce an answer."""


class OpenRouterGenerator:
    """Chat-completions generator over the OpenRouter HTTP API.

    Stateless: each call is a fresh HTTP request. That is slower than a
    persistent client but keeps the engine free of hidden connections and
    makes the class safe to share.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = DEFAULT_TIMEOUT,
        temperature: float = 0.1,
        max_context_chars: int = 6000,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.endpoint = endpoint
        self.timeout = timeout
        self.temperature = temperature
        self.max_context_chars = max_context_chars

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def __call__(self, query: str, sources: Sequence[dict]) -> str:
        if not self.available:
            raise GeneratorError("OPENROUTER_API_KEY is not set")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": build_context_prompt(query, sources, self.max_context_chars)},
            ],
            "temperature": self.temperature,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/aig",
                "X-Title": "AIG RAG",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise GeneratorError(f"HTTP {exc.code}: {detail}") from exc
        except Exception as exc:  # noqa: BLE001 - normalised for the caller
            raise GeneratorError(f"{type(exc).__name__}: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise GeneratorError(f"unexpected response shape: {list(data)[:6]}") from exc


_SYSTEM_PROMPT = (
    "Eres el motor de respuesta de un sistema de agentes. Respondes en el "
    "idioma de la pregunta. Usa exclusivamente el contexto proporcionado; si "
    "el contexto no contiene la respuesta, dilo con claridad en lugar de "
    "inventarla. Cita los fragmentos como [n] cuando los uses. Sé conciso."
)


def build_context_prompt(
    query: str, sources: Sequence[dict], max_chars: int = 6000
) -> str:
    """Render query plus retrieved sources into a single user message."""
    blocks: list[str] = []
    used = 0
    for number, source in enumerate(sources, start=1):
        title = str(source.get("title") or source.get("doc_id") or "documento")
        body = str(source.get("content") or "")
        category = str(source.get("category") or "")
        header = f"[{number}] {title}" + (f" ({category})" if category else "")
        remaining = max_chars - used
        if remaining <= 0:
            break
        block = f"{header}\n{body[:remaining]}"
        blocks.append(block)
        used += len(block)
    context = "\n\n".join(blocks) if blocks else "(sin contexto recuperable)"
    return f"Pregunta: {query}\n\nContexto:\n{context}"


def generator_from_env(
    model: str | None = None, **kwargs
) -> OpenRouterGenerator | None:
    """Return a generator configured from the environment, or ``None``.

    Returning ``None`` rather than raising lets ``RAGEngine`` stay usable with
    no credentials configured; the extractive path takes over silently.
    """
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return None
    return OpenRouterGenerator(
        model=model or os.environ.get("AIG_MODEL", DEFAULT_MODEL),
        api_key=key,
        **kwargs,
    )

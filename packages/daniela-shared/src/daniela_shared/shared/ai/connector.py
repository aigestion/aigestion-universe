"""Abstract AI connector base class and provider implementations."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Standard response from any AI connector."""

    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class AIError(Exception):
    """Base error for AI connector operations."""


class RateLimitError(AIError):
    """Raised when provider rate limit is hit."""

    def __init__(self, retry_after: float = 60.0, provider: str = ""):
        self.retry_after = retry_after
        self.provider = provider
        super().__init__(f"Rate limited by {provider}, retry after {retry_after}s")


class ModelNotFoundError(AIError):
    """Raised when requested model is not available."""


class AIConnector(ABC):
    """Abstract base class for AI model connectors."""

    def __init__(self, provider: str, api_key: str = "", model: str = "") -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self._request_count = 0
        self._error_count = 0
        self._last_request_time = 0.0

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> AIResponse:
        """Send a chat completion request."""

    @abstractmethod
    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Generate embeddings for a list of texts."""

    @abstractmethod
    def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Send a text completion request."""

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Check provider health status."""

    async def chat_async(self, messages: list[dict[str, str]], **kwargs: Any) -> AIResponse:
        """Async wrapper for chat."""
        return await asyncio.to_thread(self.chat, messages, **kwargs)

    async def embed_async(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Async wrapper for embed."""
        return await asyncio.to_thread(self.embed, texts, **kwargs)

    async def complete_async(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Async wrapper for complete."""
        return await asyncio.to_thread(self.complete, prompt, **kwargs)

    def _track_request(self, success: bool, latency_ms: float) -> None:
        self._request_count += 1
        self._last_request_time = time.time()
        if not success:
            self._error_count += 1

    @staticmethod
    def _hash_prompt(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]


class OpenAIConnector(AIConnector):
    """Connector for OpenAI API (gpt-4, gpt-3.5-turbo, text-embedding-3-small)."""

    def __init__(self, api_key: str, model: str = "gpt-4") -> None:
        super().__init__(provider="openai", api_key=api_key, model=model)
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError as e:
                raise AIError("openai package not installed: pip install openai") from e
        return self._client

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> AIResponse:
        start = time.monotonic()
        try:
            client = self._get_client()
            model = kwargs.pop("model", self.model)
            resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
            latency = (time.monotonic() - start) * 1000
            content = resp.choices[0].message.content or ""
            usage = getattr(resp, "usage", None)
            response = AIResponse(
                content=content,
                model=model,
                provider=self.provider,
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
                latency_ms=latency,
            )
            self._track_request(True, latency)
            return response
        except Exception as e:
            self._track_request(False, (time.monotonic() - start) * 1000)
            raise AIError(f"OpenAI chat failed: {e}") from e

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        try:
            client = self._get_client()
            model = kwargs.pop("model", "text-embedding-3-small")
            resp = client.embeddings.create(model=model, input=texts, **kwargs)
            return [item.embedding for item in resp.data]
        except Exception as e:
            raise AIError(f"OpenAI embed failed: {e}") from e

    def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        start = time.monotonic()
        try:
            client = self._get_client()
            model = kwargs.pop("model", self.model)
            resp = client.completions.create(model=model, prompt=prompt, **kwargs)
            latency = (time.monotonic() - start) * 1000
            content = resp.choices[0].text or ""
            usage = getattr(resp, "usage", None)
            response = AIResponse(
                content=content,
                model=model,
                provider=self.provider,
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
                latency_ms=latency,
            )
            self._track_request(True, latency)
            return response
        except Exception as e:
            self._track_request(False, (time.monotonic() - start) * 1000)
            raise AIError(f"OpenAI complete failed: {e}") from e

    async def health(self) -> dict[str, Any]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10,
                )
                return {"status": "healthy" if resp.status_code == 200 else "unhealthy", "provider": self.provider}
        except Exception as e:
            return {"status": "unhealthy", "provider": self.provider, "error": str(e)}


class ClaudeConnector(AIConnector):
    """Connector for Anthropic API (claude-3-opus, claude-3-sonnet)."""

    def __init__(self, api_key: str, model: str = "claude-3-opus") -> None:
        super().__init__(provider="anthropic", api_key=api_key, model=model)
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError as e:
                raise AIError("anthropic package not installed: pip install anthropic") from e
        return self._client

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> AIResponse:
        start = time.monotonic()
        try:
            client = self._get_client()
            model = kwargs.pop("model", self.model)
            system_msg = kwargs.pop("system", "")
            max_tokens = kwargs.pop("max_tokens", 4096)
            claude_messages = [m for m in messages if m.get("role") != "system"]
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=claude_messages,
                system=system_msg,
                **kwargs,
            )
            latency = (time.monotonic() - start) * 1000
            content = resp.content[0].text if resp.content else ""
            response = AIResponse(
                content=content,
                model=model,
                provider=self.provider,
                input_tokens=resp.usage.input_tokens,
                output_tokens=resp.usage.output_tokens,
                latency_ms=latency,
            )
            self._track_request(True, latency)
            return response
        except Exception as e:
            self._track_request(False, (time.monotonic() - start) * 1000)
            raise AIError(f"Claude chat failed: {e}") from e

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        raise AIError("Claude does not support embedding via API")

    def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)

    async def health(self) -> dict[str, Any]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    timeout=10,
                )
                return {"status": "healthy" if resp.status_code == 200 else "unhealthy", "provider": self.provider}
        except Exception as e:
            return {"status": "unhealthy", "provider": self.provider, "error": str(e)}


class OllamaConnector(AIConnector):
    """Connector for local Ollama API (llama3, mistral, codellama)."""

    def __init__(self, api_key: str = "", model: str = "llama3", base_url: str = "http://localhost:11434") -> None:
        super().__init__(provider="ollama", api_key="", model=model)
        self._base_url = base_url.rstrip("/")
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(base_url=self._base_url, timeout=60.0)
            except ImportError as e:
                raise AIError("httpx package not installed: pip install httpx") from e
        return self._client

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> AIResponse:
        start = time.monotonic()
        try:
            http = self._get_client()
            model = kwargs.pop("model", self.model)
            payload = {"model": model, "messages": messages, "stream": False}
            resp = http.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            latency = (time.monotonic() - start) * 1000
            content = data.get("message", {}).get("content", "")
            response = AIResponse(
                content=content,
                model=model,
                provider=self.provider,
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
                latency_ms=latency,
            )
            self._track_request(True, latency)
            return response
        except Exception as e:
            self._track_request(False, (time.monotonic() - start) * 1000)
            raise AIError(f"Ollama chat failed: {e}") from e

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        try:
            http = self._get_client()
            results = []
            for text in texts:
                model = kwargs.pop("model", self.model)
                resp = http.post("/api/embed", json={"model": model, "input": text})
                resp.raise_for_status()
                data = resp.json()
                results.append(data.get("embedding", []))
            return results
        except Exception as e:
            raise AIError(f"Ollama embed failed: {e}") from e

    def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        start = time.monotonic()
        try:
            http = self._get_client()
            model = kwargs.pop("model", self.model)
            resp = http.post("/api/generate", json={"model": model, "prompt": prompt, "stream": False})
            resp.raise_for_status()
            data = resp.json()
            latency = (time.monotonic() - start) * 1000
            response = AIResponse(
                content=data.get("response", ""),
                model=model,
                provider=self.provider,
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
                latency_ms=latency,
            )
            self._track_request(True, latency)
            return response
        except Exception as e:
            self._track_request(False, (time.monotonic() - start) * 1000)
            raise AIError(f"Ollama complete failed: {e}") from e

    async def health(self) -> dict[str, Any]:
        try:
            import httpx
            async with httpx.AsyncClient(base_url=self._base_url) as client:
                resp = await client.get("/api/tags", timeout=5)
                return {"status": "healthy" if resp.status_code == 200 else "unhealthy", "provider": self.provider}
        except Exception as e:
            return {"status": "unhealthy", "provider": self.provider, "error": str(e)}


class AzureOpenAIConnector(AIConnector):
    """Connector for Azure OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4", resource: str = "", deployment: str = "", api_version: str = "2024-02-15-preview") -> None:
        super().__init__(provider="azure_openai", api_key=api_key, model=model)
        self._resource = resource
        self._deployment = deployment or model
        self._api_version = api_version
        self._client = None

    def _get_endpoint(self) -> str:
        return f"https://{self._resource}.openai.azure.com/openai/deployments/{self._deployment}"

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AzureOpenAI
                self._client = AzureOpenAI(
                    api_key=self.api_key,
                    azure_endpoint=f"https://{self._resource}.openai.azure.com",
                    api_version=self._api_version,
                )
            except ImportError as e:
                raise AIError("openai package not installed: pip install openai") from e
        return self._client

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> AIResponse:
        start = time.monotonic()
        try:
            client = self._get_client()
            deployment = kwargs.pop("model", self._deployment)
            resp = client.chat.completions.create(model=deployment, messages=messages, **kwargs)
            latency = (time.monotonic() - start) * 1000
            content = resp.choices[0].message.content or ""
            usage = getattr(resp, "usage", None)
            response = AIResponse(
                content=content,
                model=deployment,
                provider=self.provider,
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
                latency_ms=latency,
                metadata={"resource": self._resource, "api_version": self._api_version},
            )
            self._track_request(True, latency)
            return response
        except Exception as e:
            self._track_request(False, (time.monotonic() - start) * 1000)
            raise AIError(f"Azure OpenAI chat failed: {e}") from e

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        try:
            client = self._get_client()
            deployment = kwargs.pop("model", "text-embedding-3-small")
            resp = client.embeddings.create(model=deployment, input=texts, **kwargs)
            return [item.embedding for item in resp.data]
        except Exception as e:
            raise AIError(f"Azure OpenAI embed failed: {e}") from e

    def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)

    async def health(self) -> dict[str, Any]:
        try:
            import httpx
            url = f"https://{self._resource}.openai.azure.com/openai/models"
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    headers={"api-key": self.api_key},
                    params={"api-version": self._api_version},
                    timeout=10,
                )
                return {"status": "healthy" if resp.status_code == 200 else "unhealthy", "provider": self.provider}
        except Exception as e:
            return {"status": "unhealthy", "provider": self.provider, "error": str(e)}


DEFAULT_FREELLMAPI_URL = "http://localhost:3002/v1"


class FreeLLMAPIConnector(AIConnector):
    """Connector for local FreeLLMAPI router (OpenAI-compatible, stdlib only).

    Routes through the user's FreeLLMAPI instance, which aggregates
    OpenRouter + other free-tier providers behind one /v1 endpoint.
    """

    def __init__(self, api_key: str, model: str = "", base_url: str = "") -> None:
        super().__init__(provider="freellmapi", api_key=api_key, model=model)
        import os

        self.base_url = (base_url or os.getenv("FREELLMAPI_URL", DEFAULT_FREELLMAPI_URL)).rstrip("/")

    def _post(self, path: str, payload: dict[str, Any], timeout: float = 60.0) -> dict[str, Any]:
        import json
        import urllib.error
        import urllib.request

        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            if e.code == 429:
                raise RateLimitError(provider=self.provider) from e
            if e.code == 401:
                raise AIError(f"FreeLLMAPI auth failed (bad unified key): {body}") from e
            raise AIError(f"FreeLLMAPI chat failed [{e.code}]: {body}") from e
        except Exception as e:
            raise AIError(f"FreeLLMAPI request failed: {e}") from e

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> AIResponse:
        start = time.monotonic()
        try:
            model = kwargs.pop("model", self.model) or "auto"
            data = self._post("/chat/completions", {"model": model, "messages": messages, **kwargs})
            latency = (time.monotonic() - start) * 1000
            choice = (data.get("choices") or [{}])[0]
            content = ((choice.get("message") or {}).get("content")) or ""
            usage = data.get("usage") or {}
            response = AIResponse(
                content=content,
                model=data.get("model", model),
                provider=self.provider,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency,
                metadata={"base_url": self.base_url},
            )
            self._track_request(True, latency)
            return response
        except (AIError, RateLimitError):
            self._track_request(False, (time.monotonic() - start) * 1000)
            raise
        except Exception as e:
            self._track_request(False, (time.monotonic() - start) * 1000)
            raise AIError(f"FreeLLMAPI chat failed: {e}") from e

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        try:
            model = kwargs.pop("model", "text-embedding-3-small")
            data = self._post("/embeddings", {"model": model, "input": texts, **kwargs})
            return [item["embedding"] for item in data.get("data", [])]
        except (AIError, RateLimitError):
            raise
        except Exception as e:
            raise AIError(f"FreeLLMAPI embed failed: {e}") from e

    def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    async def health(self) -> dict[str, Any]:
        def _check() -> dict[str, Any]:
            import urllib.request

            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    ok = resp.status == 200
                    return {"status": "healthy" if ok else "unhealthy", "provider": self.provider}
            except Exception as e:
                return {"status": "unhealthy", "provider": self.provider, "error": str(e)[:200]}

        return await asyncio.to_thread(_check)


CONNECTOR_MAP: dict[str, type[AIConnector]] = {
    "openai": OpenAIConnector,
    "anthropic": ClaudeConnector,
    "ollama": OllamaConnector,
    "azure_openai": AzureOpenAIConnector,
    "freellmapi": FreeLLMAPIConnector,
}


def create_connector(provider: str, api_key: str = "", model: str = "", **kwargs: Any) -> AIConnector:
    """Factory function returning the appropriate connector."""
    connector_cls = CONNECTOR_MAP.get(provider)
    if connector_cls is None:
        raise AIError(f"Unknown provider: {provider}. Available: {list(CONNECTOR_MAP.keys())}")
    if provider in ("azure_openai", "freellmapi"):
        return connector_cls(api_key=api_key, model=model, **kwargs)
    return connector_cls(api_key=api_key, model=model)

"""Real model-serving layer over stdlib urllib only (no new external deps).

Backends:
- Ollama native API (``/api/chat``, ``/api/generate``, ``/api/tags``).
- vLLM OpenAI-compatible API (``/v1/chat/completions``).
- Cloud fallback via any :class:`~aig_shared.ai.connector.AIConnector`.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from .connector import AIConnector, AIError, AIResponse

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_VLLM_URL = "http://localhost:8000"

__all__ = [
    "DEFAULT_OLLAMA_URL",
    "DEFAULT_VLLM_URL",
    "ServingError",
    "OllamaClient",
    "VLLMClient",
    "HealthCheck",
    "ModelWarmer",
    "ServingFallback",
    "SLOTracker",
    "SLOMonitor",
]


class ServingError(AIError):
    """Mapped error for serving-layer HTTP/connection failures."""


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: float = 60.0) -> dict[str, Any]:
    """POST a JSON payload and return the decoded JSON body."""
    body = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = ""
        if e.code == 404:
            raise ServingError(f"Model endpoint not found ({url}): {detail}") from e
        if e.code == 429:
            raise ServingError(f"Serving rate limited ({url}): {detail}") from e
        raise ServingError(f"Serving HTTP {e.code} for {url}: {detail}") from e
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, (TimeoutError,)) or "timed out" in str(reason).lower():
            raise ServingError(f"Serving timeout for {url}: {reason}") from e
        raise ServingError(f"Serving connection failed for {url}: {reason}") from e
    except TimeoutError as e:
        raise ServingError(f"Serving timeout for {url}: {e}") from e
    except OSError as e:
        if "timed out" in str(e).lower():
            raise ServingError(f"Serving timeout for {url}: {e}") from e
        raise ServingError(f"Serving connection failed for {url}: {e}") from e
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError as e:
        raise ServingError(f"Invalid JSON from {url}: {e}") from e
    return data if isinstance(data, dict) else {"data": data}


def _get_json(url: str, headers: dict[str, str] | None = None, timeout: float = 10.0) -> dict[str, Any]:
    """GET a URL and return the decoded JSON body."""
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = ""
        raise ServingError(f"Serving HTTP {e.code} for {url}: {detail}") from e
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, (TimeoutError,)) or "timed out" in str(reason).lower():
            raise ServingError(f"Serving timeout for {url}: {reason}") from e
        raise ServingError(f"Serving connection failed for {url}: {reason}") from e
    except TimeoutError as e:
        raise ServingError(f"Serving timeout for {url}: {e}") from e
    except OSError as e:
        # socket.timeout is an OSError subclass; treat as timeout mapping
        if "timed out" in str(e).lower():
            raise ServingError(f"Serving timeout for {url}: {e}") from e
        raise ServingError(f"Serving connection failed for {url}: {e}") from e
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError as e:
        raise ServingError(f"Invalid JSON from {url}: {e}") from e
    return data if isinstance(data, dict) else {"data": data}


class OllamaClient:
    """Thin Ollama HTTP client using stdlib urllib.

    Endpoints:
    - ``POST /api/chat`` for chat
    - ``POST /api/generate`` for single-prompt generation
    - ``GET /api/tags`` for listing local models
    """

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, timeout: float = 60.0) -> None:
        self.base_url = (base_url or DEFAULT_OLLAMA_URL).rstrip("/")
        self.timeout = timeout

    def _url(self, base_url: str | None = None) -> str:
        return (base_url or self.base_url).rstrip("/")

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        base_url: str | None = None,
        timeout: float | None = None,
        **options: Any,
    ) -> AIResponse:
        """POST /api/chat with ``{"model", "messages", "stream": False}``."""
        start = time.monotonic()
        url = f"{self._url(base_url)}/api/chat"
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if options:
            payload["options"] = options
        data = _post_json(url, payload, timeout=self.timeout if timeout is None else timeout)
        latency = (time.monotonic() - start) * 1000
        content = data.get("message", {}).get("content", "") if isinstance(data.get("message"), dict) else ""
        return AIResponse(
            content=content,
            model=model,
            provider="ollama",
            input_tokens=int(data.get("prompt_eval_count", 0) or 0),
            output_tokens=int(data.get("eval_count", 0) or 0),
            latency_ms=latency,
            metadata={"served_by": "ollama"},
        )

    def generate(
        self,
        model: str,
        prompt: str,
        base_url: str | None = None,
        timeout: float | None = None,
        **options: Any,
    ) -> AIResponse:
        """POST /api/generate with ``{"model", "prompt", "stream": False}``."""
        start = time.monotonic()
        url = f"{self._url(base_url)}/api/generate"
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if options:
            payload["options"] = options
        data = _post_json(url, payload, timeout=self.timeout if timeout is None else timeout)
        latency = (time.monotonic() - start) * 1000
        return AIResponse(
            content=data.get("response", ""),
            model=model,
            provider="ollama",
            input_tokens=int(data.get("prompt_eval_count", 0) or 0),
            output_tokens=int(data.get("eval_count", 0) or 0),
            latency_ms=latency,
            metadata={"served_by": "ollama"},
        )

    def list_models(self, base_url: str | None = None, timeout: float | None = None) -> list[str]:
        """GET /api/tags and return model names."""
        url = f"{self._url(base_url)}/api/tags"
        data = _get_json(url, timeout=self.timeout if timeout is None else timeout)
        models = data.get("models", [])
        names: list[str] = []
        for m in models:
            if isinstance(m, dict) and m.get("name"):
                names.append(m["name"])
            elif isinstance(m, str):
                names.append(m)
        return names


class VLLMClient:
    """OpenAI-compatible client for vLLM (``POST /v1/chat/completions``)."""

    def __init__(self, base_url: str = DEFAULT_VLLM_URL, api_key: str = "", timeout: float = 60.0) -> None:
        self.base_url = (base_url or DEFAULT_VLLM_URL).rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        base_url: str | None = None,
        timeout: float | None = None,
        api_key: str | None = None,
        **options: Any,
    ) -> AIResponse:
        """POST /v1/chat/completions with bearer auth."""
        start = time.monotonic()
        base = (base_url or self.base_url).rstrip("/")
        url = f"{base}/v1/chat/completions"
        payload: dict[str, Any] = {"model": model, "messages": messages}
        payload.update(options)
        headers = self._headers()
        if api_key is not None:
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            else:
                headers.pop("Authorization", None)
        data = _post_json(url, payload, headers=headers, timeout=self.timeout if timeout is None else timeout)
        latency = (time.monotonic() - start) * 1000
        content = ""
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            content = ""
        usage = data.get("usage", {}) if isinstance(data.get("usage"), dict) else {}
        return AIResponse(
            content=content,
            model=model,
            provider="vllm",
            input_tokens=int(usage.get("prompt_tokens", 0) or 0),
            output_tokens=int(usage.get("completion_tokens", 0) or 0),
            latency_ms=latency,
            metadata={"served_by": "vllm"},
        )

    def list_models(self, base_url: str | None = None, timeout: float | None = None) -> list[str]:
        """GET /v1/models and return model ids."""
        base = (base_url or self.base_url).rstrip("/")
        data = _get_json(
            f"{base}/v1/models", headers=self._headers(), timeout=self.timeout if timeout is None else timeout
        )
        items = data.get("data", [])
        return [m.get("id", "") for m in items if isinstance(m, dict) and m.get("id")]


class HealthCheck:
    """Liveness probes for local serving backends."""

    def __init__(
        self,
        ollama_client: OllamaClient | None = None,
        vllm_client: VLLMClient | None = None,
    ) -> None:
        self.ollama = ollama_client or OllamaClient()
        self.vllm = vllm_client or VLLMClient()

    def ping_ollama(self, base_url: str | None = None, timeout: float = 5.0) -> dict[str, Any]:
        start = time.monotonic()
        try:
            models = self.ollama.list_models(base_url=base_url, timeout=timeout)
            latency = (time.monotonic() - start) * 1000
            return {"ok": True, "latency_ms": round(latency, 2), "backend": "ollama", "models": len(models)}
        except (ServingError, AIError) as e:
            latency = (time.monotonic() - start) * 1000
            return {"ok": False, "latency_ms": round(latency, 2), "backend": "ollama", "error": str(e)}
        except Exception as e:  # never raise from a probe
            latency = (time.monotonic() - start) * 1000
            return {"ok": False, "latency_ms": round(latency, 2), "backend": "ollama", "error": str(e)}

    def ping_vllm(self, base_url: str | None = None, timeout: float = 5.0) -> dict[str, Any]:
        start = time.monotonic()
        try:
            models = self.vllm.list_models(base_url=base_url, timeout=timeout)
            latency = (time.monotonic() - start) * 1000
            return {"ok": True, "latency_ms": round(latency, 2), "backend": "vllm", "models": len(models)}
        except (ServingError, AIError) as e:
            latency = (time.monotonic() - start) * 1000
            return {"ok": False, "latency_ms": round(latency, 2), "backend": "vllm", "error": str(e)}
        except Exception as e:  # never raise from a probe
            latency = (time.monotonic() - start) * 1000
            return {"ok": False, "latency_ms": round(latency, 2), "backend": "vllm", "error": str(e)}


class ModelWarmer:
    """Pre-warm a model with a tiny prompt; records cold-start latency."""

    def __init__(
        self,
        ollama_client: OllamaClient | None = None,
        vllm_client: VLLMClient | None = None,
    ) -> None:
        self.ollama = ollama_client or OllamaClient()
        self.vllm = vllm_client or VLLMClient()
        self.records: dict[tuple[str, str], float] = {}
        self.history: list[dict[str, Any]] = []
        self.last_cold_start_ms: float = 0.0

    def warm(self, model: str, backend: str = "ollama", timeout: float = 120.0) -> dict[str, Any]:
        start = time.monotonic()
        try:
            tiny = [{"role": "user", "content": "ping"}]
            if backend == "vllm":
                resp = self.vllm.chat(model, tiny, timeout=timeout)
            else:
                resp = self.ollama.chat(model, tiny, timeout=timeout)
            cold_ms = (time.monotonic() - start) * 1000
            self.records[(backend, model)] = cold_ms
            self.last_cold_start_ms = cold_ms
            entry = {"model": model, "backend": backend, "cold_start_ms": round(cold_ms, 2), "ok": True}
            self.history.append(entry)
            logger.info("Warmed %s on %s in %.1fms", model, backend, cold_ms)
            return {**entry, "content": resp.content}
        except (ServingError, AIError) as e:
            cold_ms = (time.monotonic() - start) * 1000
            self.last_cold_start_ms = cold_ms
            entry = {
                "model": model,
                "backend": backend,
                "cold_start_ms": round(cold_ms, 2),
                "ok": False,
                "error": str(e),
            }
            self.history.append(entry)
            return entry

    def cold_start_ms(self, model: str, backend: str = "ollama") -> float | None:
        return self.records.get((backend, model))


@dataclass
class _BackendStats:
    latencies: deque = field(default_factory=lambda: deque(maxlen=200))
    errors: int = 0
    total: int = 0


class SLOTracker:
    """Per-backend latency ring buffer (last 200 samples) + error rate.

    Usage:
        slo.record("vllm", latency_ms=123.4, success=True)
        slo.stats("vllm")  # {"count", "p50_ms", "p99_ms", "error_rate", ...}
    """

    WINDOW = 200

    def __init__(self, window: int = 200) -> None:
        self._window = window
        self._backends: dict[str, _BackendStats] = defaultdict(lambda: _BackendStats(deque(maxlen=self._window)))

    def record(self, backend: str, latency_ms: float, success: bool = True) -> None:
        st = self._backends[backend]
        # Ensure deque honors a custom window even for lazily-created entries.
        if st.latencies.maxlen != self._window:
            st.latencies = deque(st.latencies, maxlen=self._window)
        st.latencies.append(float(latency_ms))
        st.total += 1
        if not success:
            st.errors += 1

    @staticmethod
    def _percentile(sorted_vals: list[float], pct: float) -> float:
        if not sorted_vals:
            return 0.0
        if len(sorted_vals) == 1:
            return float(sorted_vals[0])
        k = (len(sorted_vals) - 1) * (pct / 100.0)
        lo = int(k)
        hi = min(lo + 1, len(sorted_vals) - 1)
        frac = k - lo
        return float(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)

    def stats(self, backend: str) -> dict[str, Any]:
        st = self._backends.get(backend)
        if st is None or st.total == 0:
            return {"backend": backend, "count": 0, "p50_ms": 0.0, "p99_ms": 0.0, "error_rate": 0.0, "avg_ms": 0.0}
        vals = sorted(st.latencies)
        return {
            "backend": backend,
            "count": st.total,
            "p50_ms": round(self._percentile(vals, 50), 2),
            "p99_ms": round(self._percentile(vals, 99), 2),
            "error_rate": round(st.errors / st.total, 4) if st.total else 0.0,
            "avg_ms": round(sum(vals) / len(vals), 2) if vals else 0.0,
        }

    def all_stats(self) -> dict[str, dict[str, Any]]:
        return {backend: self.stats(backend) for backend in self._backends}

    def reset(self, backend: str | None = None) -> None:
        if backend is None:
            self._backends.clear()
        else:
            self._backends.pop(backend, None)


# Backwards/forwards-compatible alias.
SLOMonitor = SLOTracker


class ServingFallback:
    """Try backends in order [vllm, ollama, cloud]; first healthy wins.

    Records which backend served the request in ``last_served_by`` and in
    the response ``metadata["served_by"]``. Latency/errors feed ``slo``.
    """

    DEFAULT_ORDER = ("vllm", "ollama", "cloud")

    def __init__(
        self,
        vllm_client: VLLMClient | None = None,
        ollama_client: OllamaClient | None = None,
        cloud_connector: AIConnector | None = None,
        health: HealthCheck | None = None,
        slo: SLOTracker | None = None,
        order: tuple[str, ...] | list[str] | None = None,
    ) -> None:
        self.vllm = vllm_client
        self.ollama = ollama_client
        self.cloud = cloud_connector
        self.health = health
        self.slo = slo or SLOTracker()
        self.order: tuple[str, ...] = tuple(order) if order else self.DEFAULT_ORDER
        self.last_served_by: str | None = None
        self.attempts: list[dict[str, Any]] = []

    def _chat_backend(self, backend: str, model: str, messages: list[dict[str, str]], **kwargs: Any) -> AIResponse:
        if backend == "vllm":
            if self.vllm is None:
                raise ServingError("vLLM client not configured")
            return self.vllm.chat(model, messages, **kwargs)
        if backend == "ollama":
            if self.ollama is None:
                raise ServingError("Ollama client not configured")
            return self.ollama.chat(model, messages, **kwargs)
        if backend == "cloud":
            if self.cloud is None:
                raise ServingError("Cloud connector not configured")
            return self.cloud.chat(messages, model=model, **kwargs)
        raise ServingError(f"Unknown backend: {backend}")

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        order: list[str] | tuple[str, ...] | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Try each backend in ``order``; raise ServingError if all fail."""
        chain = list(order) if order else list(self.order)
        errors: dict[str, str] = {}
        self.attempts = []
        for backend in chain:
            start = time.monotonic()
            try:
                resp = self._chat_backend(backend, model, messages, **kwargs)
                latency = (time.monotonic() - start) * 1000
                self.slo.record(backend, resp.latency_ms or latency, success=True)
                self.last_served_by = backend
                resp.metadata = {**(resp.metadata or {}), "served_by": backend}
                self.attempts.append({"backend": backend, "ok": True})
                return resp
            except (ServingError, AIError) as e:
                latency = (time.monotonic() - start) * 1000
                self.slo.record(backend, latency, success=False)
                errors[backend] = str(e)
                self.attempts.append({"backend": backend, "ok": False, "error": str(e)})
                logger.warning("Serving backend %s failed: %s", backend, e)
                continue
        raise ServingError(f"All serving backends failed: {errors}")

    def complete(self, model: str, prompt: str, **kwargs: Any) -> AIResponse:
        """Single-prompt convenience wrapper over :meth:`chat`."""
        order = kwargs.pop("order", None)
        return self.chat(model, [{"role": "user", "content": prompt}], order=order, **kwargs)

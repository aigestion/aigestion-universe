"""High-level ModelService: route -> cache -> serving fallback -> cache + cost tracking.

Never raises on backend outage: returns a degraded AIResponse with
``metadata["served_by"] == "none"`` and ``metadata["degraded"] is True``.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from .cache import AICache
from .connector import AIError, AIResponse
from .registry import ModelRegistry
from .router import ModelRouter
from .serving import ServingFallback

logger = logging.getLogger(__name__)

__all__ = ["ModelService"]


class ModelService:
    """Orchestrates router + cache + serving fallback with cost tracking."""

    def __init__(
        self,
        registry: ModelRegistry | None = None,
        router: ModelRouter | None = None,
        cache: AICache | None = None,
        fallback: ServingFallback | None = None,
        serving_fallback: ServingFallback | None = None,
    ) -> None:
        self.registry = registry or ModelRegistry()
        self.router = router or ModelRouter(self.registry)
        self.cache = cache or AICache()
        # Accept both `fallback` and `serving_fallback` kwarg names.
        self.fallback = fallback or serving_fallback or ServingFallback()
        self._total_requests = 0
        self._cache_hits = 0
        self._degraded_count = 0
        self._total_cost = 0.0
        self._total_latency_ms = 0.0

    def _cache_key(self, task_type: str, prompt: str, model: str) -> str:
        return AICache.hash_prompt(json.dumps({"task": task_type, "prompt": prompt, "model": model}, sort_keys=True))

    @staticmethod
    def _response_to_dict(resp: AIResponse) -> dict[str, Any]:
        return {
            "content": resp.content,
            "model": resp.model,
            "provider": resp.provider,
            "input_tokens": resp.input_tokens,
            "output_tokens": resp.output_tokens,
            "latency_ms": resp.latency_ms,
            "metadata": resp.metadata,
        }

    def complete(self, task_type: str, prompt: str, max_cost: float | None = None, **kwargs: Any) -> AIResponse:
        """Route, check cache, call serving fallback, cache + track cost.

        Never raises: on total outage returns degraded response with
        served_by="none" and the error message in metadata.
        """
        start = time.monotonic()
        try:
            routing = self.router.route_request(task_type, max_cost=max_cost)
        except AIError as e:
            return self._degraded("", "unknown", str(e), (time.monotonic() - start) * 1000)

        model_name = routing.model.name
        provider = routing.provider
        key = self._cache_key(task_type, prompt, model_name)

        try:
            cached = self.cache.get(key)
        except Exception as e:  # cache backend must never break serving
            logger.warning("Cache get failed: %s", e)
            cached = None
        if cached:
            self._total_requests += 1
            self._cache_hits += 1
            try:
                resp = AIResponse(**cached)
            except TypeError:
                resp = AIResponse(content=str(cached.get("content", "")), model=model_name, provider=provider)
            resp.metadata = {**(resp.metadata or {}), "cached": True}
            if "served_by" not in resp.metadata:
                resp.metadata["served_by"] = self.fallback.last_served_by or provider
            return resp

        messages = [{"role": "user", "content": prompt}]
        try:
            resp = self.fallback.chat(model_name, messages, **kwargs)
            latency = (time.monotonic() - start) * 1000
            if not resp.latency_ms:
                resp.latency_ms = latency
            cost = self.registry.estimate_cost(model_name, resp.input_tokens, resp.output_tokens)
            self._total_requests += 1
            self._total_cost += cost
            self._total_latency_ms += resp.latency_ms
            try:
                self.router.record_success(resp.metadata.get("served_by", provider), resp.latency_ms)
            except Exception:
                pass
            try:
                self.cache.set(key, self._response_to_dict(resp))
            except Exception as e:
                logger.warning("Cache set failed: %s", e)
            return resp
        except AIError as e:
            latency = (time.monotonic() - start) * 1000
            try:
                self.router.record_failure(provider)
            except Exception:
                pass
            return self._degraded(model_name, provider, str(e), latency)
        except Exception as e:  # never raise on backend down
            latency = (time.monotonic() - start) * 1000
            return self._degraded(model_name, provider, str(e), latency)

    def _degraded(self, model: str, provider: str, error: str, latency_ms: float) -> AIResponse:
        self._total_requests += 1
        self._degraded_count += 1
        logger.warning("ModelService degraded (model=%s): %s", model, error)
        return AIResponse(
            content="",
            model=model,
            provider=provider,
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            metadata={"served_by": "none", "degraded": True, "error": error},
        )

    def get_stats(self) -> dict[str, Any]:
        avg = self._total_latency_ms / self._total_requests if self._total_requests else 0.0
        return {
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "degraded_count": self._degraded_count,
            "total_cost": round(self._total_cost, 8),
            "avg_latency_ms": round(avg, 2),
            "last_served_by": self.fallback.last_served_by,
        }

"""AI middleware for Flask routes with caching, retry, cost tracking."""

from __future__ import annotations

import functools
import json
import logging
import time
from collections.abc import Callable
from typing import Any

from .cache import AICache
from .connector import AIConnector, AIError, AIResponse, RateLimitError
from .registry import ModelRegistry

logger = logging.getLogger(__name__)


class AIMiddleware:
    """Middleware wrapping Flask routes with AI capabilities."""

    def __init__(
        self,
        connectors: dict[str, AIConnector] | None = None,
        registry: ModelRegistry | None = None,
        cache: AICache | None = None,
        default_model: str = "gpt-3.5-turbo",
        max_retries: int = 3,
        rate_limit_per_minute: int = 60,
    ) -> None:
        self._connectors = connectors or {}
        self._registry = registry or ModelRegistry()
        self._cache = cache or AICache()
        self._default_model = default_model
        self._max_retries = max_retries
        self._rate_limit_per_minute = rate_limit_per_minute
        self._request_log: list[dict[str, Any]] = []
        self._total_tokens = 0
        self._total_cost = 0.0
        self._minute_requests: list[float] = []

    def _get_connector(self, provider: str) -> AIConnector:
        connector = self._connectors.get(provider)
        if not connector:
            raise AIError(f"No connector registered for provider: {provider}")
        return connector

    def _check_rate_limit(self) -> None:
        now = time.time()
        self._minute_requests = [t for t in self._minute_requests if now - t < 60]
        if len(self._minute_requests) >= self._rate_limit_per_minute:
            raise RateLimitError(retry_after=60.0 - (now - self._minute_requests[0]))
        self._minute_requests.append(now)

    def _call_with_retry(self, connector: AIConnector, method: str, *args: Any, **kwargs: Any) -> Any:
        last_error = None
        for attempt in range(self._max_retries):
            try:
                self._check_rate_limit()
                fn = getattr(connector, method)
                result = fn(*args, **kwargs)
                return result
            except RateLimitError as e:
                last_error = e
                logger.warning("Rate limited on attempt %d, retrying in %.1fs", attempt + 1, e.retry_after)
                time.sleep(min(e.retry_after, 30))
            except AIError as e:
                last_error = e
                logger.warning("AI error on attempt %d: %s", attempt + 1, e)
                if attempt < self._max_retries - 1:
                    time.sleep(2 ** attempt)
        raise last_error or AIError("All retry attempts failed")

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        cache: bool = True,
        **kwargs: Any,
    ) -> AIResponse:
        model_name = model or self._default_model
        cache_key = AICache.hash_prompt(json.dumps(messages, sort_keys=True))

        if cache:
            cached = self._cache.get(cache_key)
            if cached:
                logger.info("Cache hit for model %s", model_name)
                return AIResponse(**cached)

        model_info = self._registry.get_model(model_name)
        provider = model_info.provider if model_info else "openai"
        connector = self._get_connector(provider)

        start = time.monotonic()
        response = self._call_with_retry(connector, "chat", messages, model=model_name, **kwargs)
        latency = (time.monotonic() - start) * 1000

        cost = self._registry.estimate_cost(model_name, response.input_tokens, response.output_tokens)
        self._total_tokens += response.input_tokens + response.output_tokens
        self._total_cost += cost

        self._request_log.append({
            "model": model_name,
            "provider": provider,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost": cost,
            "latency_ms": latency,
            "timestamp": time.time(),
        })

        if cache:
            self._cache.set(cache_key, {
                "content": response.content,
                "model": response.model,
                "provider": response.provider,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "latency_ms": response.latency_ms,
                "metadata": response.metadata,
            })

        return response

    def embed(self, texts: list[str], model: str = "text-embedding-3-small", **kwargs: Any) -> list[list[float]]:
        cache_key = AICache.hash_prompt(json.dumps(texts))
        cached = self._cache.get(f"embed:{cache_key}")
        if cached:
            return cached.get("embeddings", [])

        model_info = self._registry.get_model(model)
        provider = model_info.provider if model_info else "openai"
        connector = self._get_connector(provider)
        embeddings = self._call_with_retry(connector, "embed", texts, model=model, **kwargs)

        self._cache.set(f"embed:{cache_key}", {"embeddings": embeddings})
        return embeddings

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_requests": len(self._request_log),
            "total_tokens": self._total_tokens,
            "total_cost": round(self._total_cost, 6),
            "cache_size": self._cache.size(),
        }


def ai_enhanced(
    model: str = "gpt-3.5-turbo",
    cache: bool = True,
    fallback: str | None = None,
    max_retries: int = 3,
) -> Callable:
    """Decorator to wrap a Flask route with AI capabilities.

    The decorated function receives (request_text, **context) and returns the AI response.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request_text: str, *args: Any, **kwargs: Any) -> AIResponse:
            middleware = AIMiddleware(default_model=model, max_retries=max_retries)
            try:
                messages = [{"role": "user", "content": request_text}]
                result = middleware.chat(messages, model=model, cache=cache)
                return result
            except AIError:
                if fallback:
                    try:
                        messages = [{"role": "user", "content": request_text}]
                        result = middleware.chat(messages, model=fallback, cache=cache)
                        return result
                    except AIError:
                        raise
                raise
        return wrapper
    return decorator

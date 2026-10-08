"""Intelligent AI model routing with load balancing and circuit breaker."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .connector import AIConnector, AIError
from .registry import ModelInfo, ModelRegistry

logger = logging.getLogger(__name__)


class CircuitOpen(AIError):
    """Raised when circuit breaker is open for a provider."""


@dataclass
class ProviderStats:
    """Tracks per-provider statistics for routing decisions."""

    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    last_error_time: float = 0.0
    circuit_open_until: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count

    @property
    def error_rate(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count

    @property
    def is_circuit_open(self) -> bool:
        return time.time() < self.circuit_open_until


@dataclass
class RoutingResult:
    """Result of a routing decision."""

    model: ModelInfo
    provider: str
    reason: str
    fallbacks: list[str] = field(default_factory=list)


class ModelRouter:
    """Routes AI requests intelligently based on task type, cost, latency, availability."""

    def __init__(
        self,
        registry: ModelRegistry,
        circuit_threshold: int = 5,
        circuit_timeout: float = 300.0,
        weight_latency: float = 0.4,
        weight_cost: float = 0.3,
        weight_error_rate: float = 0.3,
    ) -> None:
        self.registry = registry
        self._circuit_threshold = circuit_threshold
        self._circuit_timeout = circuit_timeout
        self._weight_latency = weight_latency
        self._weight_cost = weight_cost
        self._weight_error_rate = weight_error_rate
        self._stats: dict[str, ProviderStats] = defaultdict(ProviderStats)
        self._connectors: dict[str, AIConnector] = {}

    def register_connector(self, provider: str, connector: AIConnector) -> None:
        self._connectors[provider] = connector

    def record_success(self, provider: str, latency_ms: float) -> None:
        stats = self._stats[provider]
        stats.request_count += 1
        stats.total_latency_ms += latency_ms

    def record_failure(self, provider: str) -> None:
        stats = self._stats[provider]
        stats.request_count += 1
        stats.error_count += 1
        stats.last_error_time = time.time()
        if stats.error_count >= self._circuit_threshold:
            stats.circuit_open_until = time.time() + self._circuit_timeout
            logger.warning("Circuit breaker OPEN for provider %s for %.0fs", provider, self._circuit_timeout)

    def reset_circuit(self, provider: str) -> None:
        self._stats[provider].circuit_open_until = 0.0

    def _score_model(self, model: ModelInfo, max_cost: float | None = None) -> float:
        """Lower score is better. Combines latency, cost, and error rate."""
        stats = self._stats.get(model.provider, ProviderStats())
        if stats.is_circuit_open:
            return 999.0
        latency_score = stats.avg_latency_ms / 1000.0
        cost_score = model.cost_per_1k_input + model.cost_per_1k_output
        if max_cost is not None and cost_score > max_cost:
            return 999.0
        error_score = stats.error_rate
        return (
            self._weight_latency * latency_score
            + self._weight_cost * cost_score * 1000
            + self._weight_error_rate * error_score * 100
        )

    def route_request(
        self,
        task_type: str,
        priority: str = "balanced",
        max_cost: float | None = None,
    ) -> RoutingResult:
        """Route a request and return the best model."""
        candidates = self.registry.list_models(capability=task_type) if task_type != "cost_effective" else self.registry.list_models()
        if not candidates:
            candidates = self.registry.list_models()

        ranked = sorted(candidates, key=lambda m: self._score_model(m, max_cost))
        best = ranked[0] if ranked else None
        if not best:
            raise AIError(f"No available model for task type: {task_type}")

        fallbacks = [m.name for m in ranked[1:3]]
        return RoutingResult(
            model=best,
            provider=best.provider,
            reason=f"Best match for {task_type} with priority={priority}",
            fallbacks=fallbacks,
        )

    def get_next_fallback(self, failed_provider: str, task_type: str) -> ModelInfo | None:
        """Get the next model from a different provider after failure."""
        for model in self.registry.list_models(capability=task_type):
            if model.provider != failed_provider and not self._stats[model.provider].is_circuit_open:
                return model
        return None

    def get_provider_stats(self) -> dict[str, dict[str, Any]]:
        result = {}
        for provider, stats in self._stats.items():
            result[provider] = {
                "request_count": stats.request_count,
                "error_count": stats.error_count,
                "avg_latency_ms": round(stats.avg_latency_ms, 2),
                "error_rate": round(stats.error_rate, 4),
                "circuit_open": stats.is_circuit_open,
            }
        return result

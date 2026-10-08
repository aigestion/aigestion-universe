"""AI model registry with pre-registered models and smart routing."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a registered AI model."""

    name: str
    provider: str
    endpoint: str = ""
    max_tokens: int = 4096
    context_window: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    capabilities: list[str] = field(default_factory=list)
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 100000


DEFAULT_MODELS: list[ModelInfo] = [
    ModelInfo(
        name="gpt-4",
        provider="openai",
        max_tokens=8192,
        context_window=128000,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        capabilities=["chat", "vision"],
        rate_limit_rpm=60,
        rate_limit_tpm=150000,
    ),
    ModelInfo(
        name="gpt-3.5-turbo",
        provider="openai",
        max_tokens=4096,
        context_window=16385,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        capabilities=["chat", "embed"],
        rate_limit_rpm=60,
        rate_limit_tpm=150000,
    ),
    ModelInfo(
        name="text-embedding-3-small",
        provider="openai",
        max_tokens=8191,
        context_window=8191,
        cost_per_1k_input=0.00002,
        cost_per_1k_output=0,
        capabilities=["embed"],
        rate_limit_rpm=200,
        rate_limit_tpm=1000000,
    ),
    ModelInfo(
        name="claude-3-opus",
        provider="anthropic",
        max_tokens=4096,
        context_window=200000,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        capabilities=["chat", "vision"],
        rate_limit_rpm=40,
        rate_limit_tpm=100000,
    ),
    ModelInfo(
        name="claude-3-sonnet",
        provider="anthropic",
        max_tokens=4096,
        context_window=200000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        capabilities=["chat", "vision"],
        rate_limit_rpm=60,
        rate_limit_tpm=100000,
    ),
    ModelInfo(
        name="llama3",
        provider="ollama",
        max_tokens=4096,
        context_window=8192,
        cost_per_1k_input=0,
        cost_per_1k_output=0,
        capabilities=["chat", "code"],
        rate_limit_rpm=999,
        rate_limit_tpm=999999,
    ),
    ModelInfo(
        name="mistral",
        provider="ollama",
        max_tokens=4096,
        context_window=8192,
        cost_per_1k_input=0,
        cost_per_1k_output=0,
        capabilities=["chat", "code"],
        rate_limit_rpm=999,
        rate_limit_tpm=999999,
    ),
    ModelInfo(
        name="codellama",
        provider="ollama",
        max_tokens=4096,
        context_window=16384,
        cost_per_1k_input=0,
        cost_per_1k_output=0,
        capabilities=["code", "chat"],
        rate_limit_rpm=999,
        rate_limit_tpm=999999,
    ),
]


class ModelRegistry:
    """Registry of available AI models with smart routing and cost estimation."""

    def __init__(self, models: list[ModelInfo] | None = None) -> None:
        self._models: dict[str, ModelInfo] = {}
        self._task_preferences: dict[str, list[str]] = {
            "chat": ["gpt-4", "claude-3-opus", "claude-3-sonnet", "gpt-3.5-turbo", "llama3"],
            "code": ["codellama", "gpt-4", "llama3", "mistral", "gpt-3.5-turbo"],
            "embed": ["text-embedding-3-small"],
            "vision": ["gpt-4", "claude-3-opus", "claude-3-sonnet"],
            "cost_effective": ["gpt-3.5-turbo", "llama3", "mistral", "claude-3-sonnet"],
        }
        for model in (models or DEFAULT_MODELS):
            self._models[model.name] = model

    def register_model(self, model: ModelInfo) -> None:
        self._models[model.name] = model
        logger.info("Registered model: %s (provider=%s)", model.name, model.provider)

    def get_model(self, name: str) -> ModelInfo | None:
        return self._models.get(name)

    def list_models(self, provider: str | None = None, capability: str | None = None) -> list[ModelInfo]:
        models = list(self._models.values())
        if provider:
            models = [m for m in models if m.provider == provider]
        if capability:
            models = [m for m in models if capability in m.capabilities]
        return models

    def route_to_best_model(self, task_type: str, prefer_cost: bool = False) -> ModelInfo | None:
        """Route to the best model for a given task type."""
        if prefer_cost:
            task_type = "cost_effective"
        preferences = self._task_preferences.get(task_type, [])
        for name in preferences:
            model = self._models.get(name)
            if model:
                return model
        fallback = list(self._models.values())
        return fallback[0] if fallback else None

    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for a given model and token counts."""
        model = self._models.get(model_name)
        if not model:
            return 0.0
        input_cost = (input_tokens / 1000.0) * model.cost_per_1k_input
        output_cost = (output_tokens / 1000.0) * model.cost_per_1k_output
        return round(input_cost + output_cost, 8)

    def get_fallback_chain(self, primary_model: str) -> list[str]:
        """Return a list of fallback models if the primary fails."""
        primary = self._models.get(primary_model)
        if not primary:
            return []
        chain = []
        for name, model in self._models.items():
            if name != primary_model and set(model.capabilities).intersection(set(primary.capabilities)):
                chain.append(name)
        return chain

    def set_task_preferences(self, task_type: str, model_order: list[str]) -> None:
        self._task_preferences[task_type] = model_order

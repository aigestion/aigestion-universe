"""AI module for aig: connectors, registry, router, cache, and middleware."""

from .cache import AICache
from .connector import (
    DEFAULT_FREELLMAPI_URL,
    AIConnector,
    AIError,
    AIResponse,
    AzureOpenAIConnector,
    ClaudeConnector,
    FreeLLMAPIConnector,
    OllamaConnector,
    OpenAIConnector,
    RateLimitError,
    create_connector,
)
from .middleware import AIMiddleware, ai_enhanced
from .providers import PROVIDER_ORDER, PROVIDERS
from .registry import ModelInfo, ModelRegistry
from .router import CircuitOpen, ModelRouter, RoutingResult
from .service import ModelService
from .serving import (
    DEFAULT_OLLAMA_URL,
    DEFAULT_VLLM_URL,
    HealthCheck,
    ModelWarmer,
    OllamaClient,
    ServingError,
    ServingFallback,
    SLOMonitor,
    SLOTracker,
    VLLMClient,
)

__all__ = [
    "AIConnector",
    "AIError",
    "AIResponse",
    "AIMiddleware",
    "AICache",
    "AzureOpenAIConnector",
    "ClaudeConnector",
    "CircuitOpen",
    "DEFAULT_FREELLMAPI_URL",
    "DEFAULT_OLLAMA_URL",
    "DEFAULT_VLLM_URL",
    "HealthCheck",
    "ModelInfo",
    "ModelRegistry",
    "ModelRouter",
    "ModelService",
    "ModelWarmer",
    "OpenAIConnector",
    "OllamaConnector",
    "OllamaClient",
    "PROVIDERS",
    "PROVIDER_ORDER",
    "RateLimitError",
    "RoutingResult",
    "ServingError",
    "FreeLLMAPIConnector",
    "ServingFallback",
    "SLOTracker",
    "SLOMonitor",
    "VLLMClient",
    "ai_enhanced",
    "create_connector",
]

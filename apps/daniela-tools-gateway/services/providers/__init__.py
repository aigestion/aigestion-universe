"""Provider adapters for the BYOK tools gateway.

Every adapter implements the same `Provider` protocol so the gateway
can route a call to any backend without the caller caring which one
served it.
"""
from .base import Provider, ProviderResponse, ProviderKind
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .local import LocalProvider

__all__ = [
    "Provider",
    "ProviderResponse",
    "ProviderKind",
    "OpenAIProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "LocalProvider",
]

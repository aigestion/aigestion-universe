"""Provider configurations for AI models."""

from typing import Any

PROVIDERS: dict[str, dict[str, Any]] = {
    "openai": {
        "api_url": "https://api.openai.com/v1",
        "health_endpoint": "/models",
        "models": {
            "gpt-4": {
                "max_tokens": 8192,
                "context_window": 128000,
                "cost_per_1k_input": 0.03,
                "cost_per_1k_output": 0.06,
                "capabilities": ["chat", "vision"],
                "rate_limit_rpm": 60,
                "rate_limit_tpm": 150000,
            },
            "gpt-3.5-turbo": {
                "max_tokens": 4096,
                "context_window": 16385,
                "cost_per_1k_input": 0.0005,
                "cost_per_1k_output": 0.0015,
                "capabilities": ["chat", "embed"],
                "rate_limit_rpm": 60,
                "rate_limit_tpm": 150000,
            },
            "text-embedding-3-small": {
                "max_tokens": 8191,
                "context_window": 8191,
                "cost_per_1k_input": 0.00002,
                "cost_per_1k_output": 0,
                "capabilities": ["embed"],
                "rate_limit_rpm": 200,
                "rate_limit_tpm": 1000000,
            },
        },
    },
    "anthropic": {
        "api_url": "https://api.anthropic.com/v1",
        "health_endpoint": "/models",
        "models": {
            "claude-3-opus": {
                "max_tokens": 4096,
                "context_window": 200000,
                "cost_per_1k_input": 0.015,
                "cost_per_1k_output": 0.075,
                "capabilities": ["chat", "vision"],
                "rate_limit_rpm": 40,
                "rate_limit_tpm": 100000,
            },
            "claude-3-sonnet": {
                "max_tokens": 4096,
                "context_window": 200000,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015,
                "capabilities": ["chat", "vision"],
                "rate_limit_rpm": 60,
                "rate_limit_tpm": 100000,
            },
        },
    },
    "ollama": {
        "api_url": "http://localhost:11434/v1",
        "health_endpoint": "/tags",
        "models": {
            "llama3": {
                "max_tokens": 4096,
                "context_window": 8192,
                "cost_per_1k_input": 0,
                "cost_per_1k_output": 0,
                "capabilities": ["chat", "code"],
                "rate_limit_rpm": 999,
                "rate_limit_tpm": 999999,
            },
            "mistral": {
                "max_tokens": 4096,
                "context_window": 8192,
                "cost_per_1k_input": 0,
                "cost_per_1k_output": 0,
                "capabilities": ["chat", "code"],
                "rate_limit_rpm": 999,
                "rate_limit_tpm": 999999,
            },
            "codellama": {
                "max_tokens": 4096,
                "context_window": 16384,
                "cost_per_1k_input": 0,
                "cost_per_1k_output": 0,
                "capabilities": ["code", "chat"],
                "rate_limit_rpm": 999,
                "rate_limit_tpm": 999999,
            },
        },
    },
    "azure_openai": {
        "api_url": "https://{resource}.openai.azure.com/openai/deployments/{deployment}",
        "health_endpoint": "/models",
        "models": {
            "gpt-4": {
                "max_tokens": 8192,
                "context_window": 128000,
                "cost_per_1k_input": 0.03,
                "cost_per_1k_output": 0.06,
                "capabilities": ["chat", "vision"],
                "rate_limit_rpm": 60,
                "rate_limit_tpm": 150000,
            },
            "gpt-35-turbo": {
                "max_tokens": 4096,
                "context_window": 16385,
                "cost_per_1k_input": 0.0005,
                "cost_per_1k_output": 0.0015,
                "capabilities": ["chat"],
                "rate_limit_rpm": 60,
                "rate_limit_tpm": 150000,
            },
            "text-embedding-3-small": {
                "max_tokens": 8191,
                "context_window": 8191,
                "cost_per_1k_input": 0.00002,
                "cost_per_1k_output": 0,
                "capabilities": ["embed"],
                "rate_limit_rpm": 200,
                "rate_limit_tpm": 1000000,
            },
        },
    },
    "freellmapi": {
        "api_url": "http://localhost:3002/v1",
        "health_endpoint": "/models",
        "models": {
            "auto": {
                "max_tokens": 4096,
                "context_window": 128000,
                "cost_per_1k_input": 0,
                "cost_per_1k_output": 0,
                "capabilities": ["chat", "code"],
                "rate_limit_rpm": 60,
                "rate_limit_tpm": 200000,
            },
        },
    },
}

PROVIDER_ORDER = ["freellmapi", "ollama", "openai", "anthropic", "azure_openai"]

TASK_MODELPreferences: dict[str, list[str]] = {
    "chat": ["auto", "gpt-4", "claude-3-opus", "claude-3-sonnet", "gpt-3.5-turbo", "llama3"],
    "code": ["auto", "codellama", "gpt-4", "llama3", "mistral", "gpt-3.5-turbo"],
    "embed": ["text-embedding-3-small"],
    "vision": ["gpt-4", "claude-3-opus", "claude-3-sonnet"],
    "cost_effective": ["auto", "gpt-3.5-turbo", "llama3", "mistral", "claude-3-sonnet"],
}

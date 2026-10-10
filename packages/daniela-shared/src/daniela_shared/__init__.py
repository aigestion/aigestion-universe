"""Daniela Shared - Shared Infrastructure for Cross-Device Sync, AI Bridge, Pixel Guard, Memory RAG."""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0"

_LAZY: dict[str, str] = {
    # AI Bridge
    "AIRegistry": "daniela_shared.ai.registry",
    "AIConnector": "daniela_shared.ai.connector",
    "AIProviders": "daniela_shared.ai.providers",
    "AIMiddleware": "daniela_shared.ai.middleware",
    "AIRouter": "daniela_shared.ai.router",
    "AICache": "daniela_shared.ai.cache",
    "AIServing": "daniela_shared.ai.serving",
    "AIService": "daniela_shared.ai.service",
    "AIBridge": "daniela_shared.ai_bridge",
    # Auth
    "AuthMiddleware": "daniela_shared.auth.middleware",
    # Config
    "EnvLoader": "daniela_shared.config.env_loader",
    # Cross-device sync
    "CrossDeviceSync": "daniela_shared.cross_device_sync",
    # DB
    "RedisPool": "daniela_shared.db.redis_pool",
    "SQLitePool": "daniela_shared.db.sqlite_pool",
    # Epic PC
    "EpicPCManager": "daniela_shared.epic_pc_manager",
    # Errors
    "DanielaError": "daniela_shared.errors",
    # Events
    "EventBus": "daniela_shared.event_bus",
    "EventType": "daniela_shared.events",
    # Logfmt
    "LogfmtEncoder": "daniela_shared.logfmt",
    # Metrics
    "MetricsCollector": "daniela_shared.metrics",
    # Pixel Guard
    "PixelGuard": "daniela_shared.pixel_guard",
    # Memory RAG
    "MemoryRAG": "daniela_shared.memory_rag",
    # Registry
    "ServiceRegistry": "daniela_shared.registry",
    # Scheduler
    "Scheduler": "daniela_shared.scheduler",
    # State
    "StateManager": "daniela_shared.state_manager",
    # Unified
    "UnifiedBridge": "daniela_shared.unified_bridge",
    "UnifiedDashboard": "daniela_shared.dashboard",
    # Voice
    "VoiceActivation": "daniela_shared.voice_activation",
    # GEV
    "GEVTools": "daniela_shared.gev_tools",
    # Health
    "HealthCheck": "daniela_shared.health",
}

__all__ = [
    "__version__",
    "AIBridge",
    "AICache",
    "AIConnector",
    "AIMiddleware",
    "AIProviders",
    "AIRouter",
    "AIRegistry",
    "AIServing",
    "AIService",
    "AuthMiddleware",
    "CrossDeviceSync",
    "DanielaError",
    "EnvLoader",
    "EpicPCManager",
    "EventBus",
    "EventType",
    "GEVTools",
    "HealthCheck",
    "LogfmtEncoder",
    "MemoryRAG",
    "MetricsCollector",
    "PixelGuard",
    "RedisPool",
    "ServiceRegistry",
    "Scheduler",
    "SQLitePool",
    "StateManager",
    "UnifiedBridge",
    "UnifiedDashboard",
    "VoiceActivation",
]


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        import importlib
        module = importlib.import_module(_LAZY[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
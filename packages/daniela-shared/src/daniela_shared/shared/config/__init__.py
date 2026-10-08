"""Configuration management for all aig services."""

# 2026-10-5: fusion de `daniela-os/shared/config.py` (plano) en este
# paquete. WEB_PORT es el puerto del servicio daniela-os (server.py).
WEB_PORT = 9200

import os
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    name: str
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1

# Service ports registry
SERVICE_PORTS = {
    "epic_pc": 5020,
    "hermes_epic": 9300,
    "aig_optimization": 9400,
    "frontend": 9500,
    "infra_opt": 9700,
    "agent_mobile": 9800,
    "sec_monitoring": 9999,
    "perf_quality": 9998,
}

def get_service_config(name: str) -> ServiceConfig:
    """Get service configuration by name."""
    port = SERVICE_PORTS.get(name, 8000)
    return ServiceConfig(name=name, port=port)

def get_database_url() -> str:
    """Get database URL from environment or default."""
    return os.getenv("DATABASE_URL", "sqlite:///aig.db")

def get_redis_url() -> str:
    """Get Redis URL from environment or default."""
    return os.getenv("REDIS_URL", "redis://:aig_redis_2026@localhost:6379/0")

def get_nats_url() -> str:
    """Get NATS URL from environment or default."""
    return os.getenv("NATS_URL", "nats://localhost:4222")

def get_freellmapi_url() -> str:
    """Get local FreeLLMAPI router URL (Docker on :3002)."""
    return os.getenv("FREELLMAPI_URL", "http://localhost:3002/v1")

def get_freellmapi_key() -> str:
    """Get FreeLLMAPI unified bearer key (freellmapi-...)."""
    return os.getenv("FREELLMAPI_KEY", "")

_INSECURE_JWT_DEFAULTS = {
    "change-me-in-production",
    "aigestion-super-secret-key-change-in-production",
    "aig-super-secret-key-change-in-production",
}


def get_jwt_secret() -> str:
    """Get JWT secret from environment. Fail-closed: sin secreto no arranca."""
    secret = os.getenv("AIGESTION_JWT_SECRET") or os.getenv("JWT_SECRET")
    if not secret or secret in _INSECURE_JWT_DEFAULTS:
        raise RuntimeError(
            "JWT_SECRET no configurado (o es el default inseguro). Define "
            "AIGESTION_JWT_SECRET o JWT_SECRET con secreto de alto entropo, p. ej. secrets.token_urlsafe(32)."
        )
    return secret

def get_service_urls() -> dict[str, str]:
    """Get all service URLs for inter-service communication."""
    base = os.getenv("SERVICE_BASE_URL", "http://localhost")
    return {
        name: f"{base}:{port}"
        for name, port in SERVICE_PORTS.items()
    }

"""Service registry for health checks and auto-registration (migrated from shared.registry)."""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("aig.registry")

@dataclass
class ServiceInfo:
    """Service registration info."""
    name: str
    host: str
    port: int
    category: str = "core"
    version: str = "1.0.0"
    status: str = "healthy"
    endpoints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class ServiceRegistry:
    """Central service registry for health checks and discovery."""

    def __init__(self, registry_port: int = 9997):
        self.registry_port = registry_port
        self._services: dict[str, ServiceInfo] = {}
        self._lock = threading.Lock()
        self._health_checks: dict[str, bool] = {}

    def register(self, service: ServiceInfo) -> bool:
        """Register a service."""
        with self._lock:
            self._services[service.name] = service
            self._health_checks[service.name] = True
            logger.info(f"Service registered: {service.name} on port {service.port}")
            return True

    def deregister(self, service_name: str) -> bool:
        """Deregister a service."""
        with self._lock:
            if service_name in self._services:
                del self._services[service_name]
                del self._health_checks[service_name]
                return True
            return False

    def get_service(self, service_name: str) -> ServiceInfo | None:
        """Get service info by name."""
        return self._services.get(service_name)

    def get_all_services(self) -> dict[str, ServiceInfo]:
        """Get all registered services."""
        return self._services.copy()

    def update_heartbeat(self, service_name: str) -> bool:
        """Update service heartbeat."""
        with self._lock:
            if service_name in self._services:
                self._services[service_name].last_heartbeat = datetime.utcnow().isoformat()
                self._services[service_name].status = "healthy"
                return True
            return False

    def check_health(self, service_name: str) -> bool:
        """Check if service is healthy (heartbeat within 30s)."""
        if service_name not in self._services:
            return False

        last_heartbeat = datetime.fromisoformat(self._services[service_name].last_heartbeat)
        now = datetime.utcnow()
        elapsed = (now - last_heartbeat).total_seconds()
        return elapsed < 30

    def get_healthy_services(self) -> list[ServiceInfo]:
        """Get all healthy services."""
        return [s for s in self._services.values() if self.check_health(s.name)]

    def get_service_status(self) -> dict[str, Any]:
        """Get status of all services."""
        status = {}
        for name, service in self._services.items():
            status[name] = {
                "name": service.name,
                "port": service.port,
                "category": service.category,
                "status": service.status,
                "healthy": self.check_health(name),
                "last_heartbeat": service.last_heartbeat,
                "endpoints": service.endpoints
            }
        return status

# Global registry
_registry: ServiceRegistry | None = None

def get_registry() -> ServiceRegistry:
    """Get global service registry instance."""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry

def register_service(
    name: str,
    host: str,
    port: int,
    category: str = "core",
    version: str = "1.0.0",
    endpoints: list[str] | None = None
) -> bool:
    """Register a service in the global registry."""
    service = ServiceInfo(
        name=name,
        host=host,
        port=port,
        category=category,
        version=version,
        endpoints=endpoints or []
    )
    return get_registry().register(service)

def update_heartbeat(service_name: str) -> bool:
    """Update heartbeat for a service."""
    return get_registry().update_heartbeat(service_name)

def get_service(name: str) -> ServiceInfo | None:
    """Get service info by name."""
    return get_registry().get_service(name)

def get_all_services() -> dict[str, ServiceInfo]:
    """Get all registered services."""
    return get_registry().get_all_services()

def get_service_status() -> dict[str, Any]:
    """Get status of all services."""
    return get_registry().get_service_status()

"""Cross-Engine Orchestrator - manages health monitoring, status, flows, and dependencies."""

import threading
import time

from .connector import EngineConnector
from .event_bus import get_event_bus
from .protocols import ALL_ENGINES, ENGINE_PORTS


class CrossEngineOrchestrator:
    """Registers all 19 engines, monitors health, tracks flows and dependencies."""

    def __init__(self) -> None:
        self._event_bus = get_event_bus()
        self._connectors: dict[str, EngineConnector] = {}
        self._health_cache: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._monitor_thread: threading.Thread | None = None
        self._running = False
        self._flows: list[dict] = []
        self._dependencies = self._build_dependency_graph()

        for engine_name, port in ENGINE_PORTS.items():
            self._connectors[engine_name] = EngineConnector(engine_name, port)

    def start(self) -> None:
        """Start health monitoring loop."""
        if self._running:
            return
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self._event_bus.publish("orchestrator", "service.startup", {"message": "orchestrator started"})

    def stop(self) -> None:
        self._running = False
        self._event_bus.publish("orchestrator", "service.shutdown", {"message": "orchestrator stopped"})

    def get_system_status(self) -> dict:
        """Return status dict for all 19 engines."""
        with self._lock:
            statuses = {}
            for name in ALL_ENGINES:
                cache = self._health_cache.get(name)
                if cache:
                    statuses[name] = cache
                else:
                    statuses[name] = {
                        "engine": name,
                        "port": ENGINE_PORTS[name],
                        "status": "unknown",
                        "last_check": 0,
                    }
            return {"engines": statuses, "total": len(statuses)}

    def get_system_health(self) -> int:
        """Return health score 0-100 (percentage of healthy engines)."""
        with self._lock:
            if not self._health_cache:
                return 0
            healthy = sum(
                1 for v in self._health_cache.values() if v.get("status") == "healthy"
            )
            total = len(self._health_cache)
            return int((healthy / total) * 100) if total else 0

    def get_cross_engine_flows(self) -> list[dict]:
        """Return recorded data flows between engines."""
        with self._lock:
            return list(self._flows[-50:])

    def get_engine_dependencies(self) -> dict:
        """Return the dependency graph."""
        return self._dependencies

    def record_flow(self, source: str, target: str, event_type: str, payload: dict = None) -> None:
        """Record a data flow between two engines."""
        flow = {
            "source": source,
            "target": target,
            "event_type": event_type,
            "timestamp": time.time(),
        }
        with self._lock:
            self._flows.append(flow)
            if len(self._flows) > 500:
                self._flows = self._flows[-500:]
        self._event_bus.publish(source, event_type, payload or {"target": target})

    def get_anomalies(self) -> list[dict]:
        """Flag engines with high error rates or circuit-open state."""
        anomalies = []
        for name, connector in self._connectors.items():
            stats = connector.get_stats()
            if stats["circuit_state"] == "open":
                anomalies.append({"engine": name, "type": "circuit_open", "details": stats})
            elif stats["errors"] > 0 and stats["requests"] > 0:
                rate = stats["errors"] / stats["requests"]
                if rate > 0.3:
                    anomalies.append({"engine": name, "type": "high_error_rate", "error_rate": round(rate, 3)})
        return anomalies

    def _monitor_loop(self) -> None:
        while self._running:
            for name, connector in self._connectors.items():
                healthy = connector.health_check()
                with self._lock:
                    self._health_cache[name] = {
                        "engine": name,
                        "port": ENGINE_PORTS[name],
                        "status": "healthy" if healthy else "unhealthy",
                        "last_check": time.time(),
                    }
                event = "service.health"
                self._event_bus.publish(name, event, {"healthy": healthy})
            time.sleep(10)

    @staticmethod
    def _build_dependency_graph() -> dict:
        """Define known inter-engine dependencies."""
        return {
            "epic_pc": ["hermes", "optimization"],
            "daniela": ["hermes", "data_engine", "secure_engine"],
            "hermes": ["security", "data_engine"],
            "optimization": ["data_engine", "perf"],
            "frontend": ["hermes", "optimization"],
            "infra_opt": ["scale_engine", "perf"],
            "agent_mobile": ["hermes", "daniela"],
            "security": ["secure_engine", "intel_engine"],
            "perf": ["data_engine"],
            "dashboard": ["hermes", "data_engine"],
            "intel_engine": ["data_engine", "security"],
            "auto_engine": ["hermes", "optimization"],
            "data_engine": [],
            "secure_engine": ["intel_engine"],
            "devtools_engine": ["perf", "data_engine"],
            "ecosystem_engine": ["hermes", "data_engine"],
            "ux_engine": ["frontend"],
            "scale_engine": ["infra_opt", "perf"],
        }

    def _check_engine(self, name: str) -> dict:
        """Check a single engine and return its status dict."""
        connector = self._connectors.get(name)
        if not connector:
            return {"engine": name, "status": "unknown", "port": 0, "last_check": 0}
        healthy = connector.health_check()
        return {
            "engine": name,
            "port": ENGINE_PORTS.get(name, 0),
            "status": "healthy" if healthy else "unhealthy",
            "last_check": time.time(),
        }

"""
Pyroscope Integration for AIG - Continuous Profiling
CPU, memory, and custom profiling for all Python services.
"""
from __future__ import annotations

import atexit
import os
from contextlib import contextmanager
from typing import Any

try:
    import pyroscope
    PYROSCOPE_AVAILABLE = True
except ImportError:
    PYROSCOPE_AVAILABLE = False
    pyroscope = None


class PyroscopeConfig:
    """Configuration for Pyroscope profiler."""

    def __init__(
        self,
        application_name: str = "aig-service",
        server_address: str = "http://localhost:4040",
        sample_rate: int = 100,
        detect_subprocesses: bool = True,
        tags: dict[str, str] | None = None,
        profile_types: list | None = None,
    ):
        self.application_name = application_name
        self.server_address = server_address
        self.sample_rate = sample_rate
        self.detect_subprocesses = detect_subprocesses
        self.tags = tags or {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "service": application_name,
            "host": os.getenv("HOSTNAME", "localhost"),
        }
        self.profile_types = profile_types or ["cpu", "memory"]


class PyroscopeProfiler:
    """Wrapper for Pyroscope continuous profiler."""

    def __init__(self, config: PyroscopeConfig):
        self.config = config
        self._started = False

    def start(self) -> bool:
        """Start the profiler."""
        if not PYROSCOPE_AVAILABLE:
            print("[Pyroscope] Not available, skipping")
            return False

        if self._started:
            return True

        try:
            pyroscope.configure(
                application_name=self.config.application_name,
                server_address=self.config.server_address,
                sample_rate=self.config.sample_rate,
                detect_subprocesses=self.config.detect_subprocesses,
                tags=self.config.tags,
                profile_types=self.config.profile_types,
            )
            self._started = True
            atexit.register(self.stop)
            print(f"[Pyroscope] Started profiling {self.config.application_name}")
            return True
        except Exception as e:
            print(f"[Pyroscope] Failed to start: {e}")
            return False

    def stop(self) -> None:
        """Stop the profiler."""
        if not PYROSCOPE_AVAILABLE or not self._started:
            return

        try:
            pyroscope.shutdown()
            self._started = False
            print(f"[Pyroscope] Stopped profiling {self.config.application_name}")
        except Exception as e:
            print(f"[Pyroscope] Error stopping: {e}")

    @contextmanager
    def profile(self, name: str, tags: dict[str, str] | None = None):
        """Context manager for profiling a code block."""
        if not PYROSCOPE_AVAILABLE or not self._started:
            yield
            return

        try:
            with pyroscope.tag_wrapper({**(self.config.tags), **(tags or {})}):
                yield
        except Exception:
            yield

    def tag(self, tags: dict[str, str]) -> None:
        """Add tags to current profiling context."""
        if PYROSCOPE_AVAILABLE and self._started:
            try:
                pyroscope.tag(**tags)
            except Exception:
                pass

    def remove_tag(self, key: str) -> None:
        """Remove a tag from current context."""
        if PYROSCOPE_AVAILABLE and self._started:
            try:
                pyroscope.remove_tag(key)
            except Exception:
                pass


# Global profiler instance
_default_profiler: PyroscopeProfiler | None = None


def init_pyroscope(
    application_name: str,
    server_address: str = "http://localhost:4040",
    tags: dict[str, str] | None = None,
    sample_rate: int = 100,
) -> PyroscopeProfiler:
    """Initialize global Pyroscope profiler."""
    global _default_profiler
    config = PyroscopeConfig(
        application_name=application_name,
        server_address=server_address,
        sample_rate=sample_rate,
        tags=tags,
    )
    _default_profiler = PyroscopeProfiler(config)
    _default_profiler.start()
    return _default_profiler


def get_profiler() -> PyroscopeProfiler | None:
    """Get global profiler instance."""
    return _default_profiler


@contextmanager
def profile_block(name: str, tags: dict[str, str] | None = None):
    """Context manager for profiling a code block using global profiler."""
    profiler = get_profiler()
    if profiler:
        with profiler.profile(name, tags):
            yield
    else:
        yield


def tag_profiling(tags: dict[str, str]) -> None:
    """Add tags to global profiler context."""
    profiler = get_profiler()
    if profiler:
        profiler.tag(tags)


def remove_profiling_tag(key: str) -> None:
    """Remove tag from global profiler context."""
    profiler = get_profiler()
    if profiler:
        profiler.remove_tag(key)


# FastAPI/Starlette middleware
class PyroscopeMiddleware:
    """Middleware to add request tags to profiling."""

    def __init__(self, app, profiler: PyroscopeProfiler | None = None):
        self.app = app
        self.profiler = profiler or get_profiler()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Add request tags
        tags = {
            "http_method": scope.get("method", ""),
            "http_path": scope.get("path", ""),
            "http_route": scope.get("route", {}).get("path", "") if scope.get("route") else "",
        }

        if self.profiler and self.profiler._started:
            self.profiler.tag(tags)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status = message.get("status", 0)
                if self.profiler and self.profiler._started:
                    self.profiler.tag({"http_status": str(status)})
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Clean up tags
            if self.profiler and self.profiler._started:
                for key in tags:
                    self.profiler.remove_tag(key)
                if "http_status" in tags:
                    self.profiler.remove_tag("http_status")


# Decorator for profiling functions
def profile_function(name: str | None = None, tags: dict[str, str] | None = None):
    """Decorator to profile a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            profiler = get_profiler()
            if not profiler or not profiler._started:
                return func(*args, **kwargs)

            func_name = name or f"{func.__module__}.{func.__qualname__}"
            profiler.tag({**(profiler.config.tags), **(tags or {}), "function": func_name})
            try:
                return func(*args, **kwargs)
            finally:
                for key in tags or {}:
                    profiler.remove_tag(key)
                profiler.remove_tag("function")
        return wrapper
    return decorator


# Service-specific initializers
def init_daniela_profiler() -> PyroscopeProfiler:
    """Initialize profiler for Daniela service."""
    return init_pyroscope(
        application_name="aig-daniela",
        tags={"service": "daniela", "component": "core"},
    )


def init_hermes_profiler() -> PyroscopeProfiler:
    """Initialize profiler for Hermes service."""
    return init_pyroscope(
        application_name="aig-hermes",
        tags={"service": "hermes", "component": "orchestrator"},
    )


def init_agent_profiler(agent_name: str) -> PyroscopeProfiler:
    """Initialize profiler for an agent."""
    return init_pyroscope(
        application_name=f"aig-agent-{agent_name}",
        tags={"service": "agent", "agent": agent_name},
    )


def init_orchestrator_profiler() -> PyroscopeProfiler:
    """Initialize profiler for orchestrator."""
    return init_pyroscope(
        application_name="aig-orchestrator",
        tags={"service": "orchestrator", "component": "control-plane"},
    )


# Health check for Pyroscope
def check_pyroscope_health(server_address: str = "http://localhost:4040") -> dict[str, Any]:
    """Check Pyroscope server health."""
    import urllib.request

    try:
        req = urllib.request.Request(f"{server_address}/ready")
        with urllib.request.urlopen(req, timeout=5) as response:
            return {
                "healthy": response.status == 200,
                "status": response.status,
            }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
        }

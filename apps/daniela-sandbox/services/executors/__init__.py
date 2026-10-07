"""Sandbox executors — pluggable isolation backends."""
from .base import Backend, ExecutionResult, Executor, SandboxConfig
from .process import ProcessExecutor

try:
    from .docker import DockerExecutor
except ImportError:
    DockerExecutor = None  # type: ignore[assignment]

__all__ = [
    "Backend",
    "ExecutionResult",
    "Executor",
    "SandboxConfig",
    "ProcessExecutor",
    "DockerExecutor",
]

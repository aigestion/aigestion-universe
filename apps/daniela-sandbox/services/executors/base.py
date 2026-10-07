"""Executor protocol and shared types."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class Backend(str, Enum):
    PROCESS = "process"
    DOCKER = "docker"


@dataclass
class SandboxConfig:
    """Resource limits for a single execution."""

    timeout_s: float = 30.0
    max_output_bytes: int = 1_048_576      # 1 MiB stdout+stderr cap
    max_memory_mb: int = 512               # best-effort memory cap
    workdir: Optional[str] = None
    network_allowed: bool = False
    env: Dict[str, str] = field(default_factory=dict)

    def truncated_output(self, text: str) -> str:
        """Clamp text to max_output_bytes (UTF-8 aware)."""
        encoded = text.encode("utf-8", "ignore")
        if len(encoded) <= self.max_output_bytes:
            return text
        return encoded[: self.max_output_bytes].decode("utf-8", "ignore")


@dataclass
class ExecutionResult:
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    timed_out: bool = False
    backend: str = Backend.PROCESS.value
    memory_bytes: int = 0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and (self.exit_code in (0, None))


class Executor(ABC):
    """Isolation backend contract."""

    backend: Backend

    @abstractmethod
    async def exec(
        self,
        command: str,
        *,
        config: Optional[SandboxConfig] = None,
    ) -> ExecutionResult:
        ...

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        ...

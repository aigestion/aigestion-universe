"""Docker executor — ephemeral container isolation.

Strongest isolation: runs each command in a throwaway container
with resource caps, no network, read-only rootfs, and a tmpfs.
"""
from __future__ import annotations

import asyncio
import shutil
import time
from typing import Any, Dict, Optional

from .base import Backend, ExecutionResult, Executor, SandboxConfig


class DockerExecutor(Executor):
    """Runs commands in an ephemeral Docker container."""

    backend = Backend.DOCKER

    def __init__(self, image: str = "python:3.13-slim") -> None:
        self.image = image
        self._docker = shutil.which("docker")

    async def exec(
        self,
        command: str,
        *,
        config: Optional[SandboxConfig] = None,
    ) -> ExecutionResult:
        cfg = config or SandboxConfig()
        if not self._docker:
            return ExecutionResult(
                backend=self.backend.value,
                error="docker not installed",
            )

        start = time.perf_counter()
        cmd = [
            self._docker, "run", "--rm",
            "--network", "none" if not cfg.network_allowed else "bridge",
            "--memory", f"{cfg.max_memory_mb}m",
            "--memory-swap", f"{cfg.max_memory_mb}m",
            "--cpus", "1",
            "--pids-limit", "128",
            "--read-only",
            "--tmpfs", "/tmp:rw,size=64m,noexec,nosuid",
            "--workdir", "/tmp",
            "--user", "nobody",
            self.image,
            "sh", "-c", command,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            return ExecutionResult(
                backend=self.backend.value,
                error=f"docker run failed: {type(e).__name__}: {e}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=cfg.timeout_s + 10
            )
        except asyncio.TimeoutError:
            await self._kill(proc)
            return ExecutionResult(
                timed_out=True,
                backend=self.backend.value,
                duration_ms=(time.perf_counter() - start) * 1000,
                error=f"timeout after {cfg.timeout_s}s",
            )

        duration_ms = (time.perf_counter() - start) * 1000
        stdout = cfg.truncated_output(stdout_b.decode("utf-8", "ignore"))
        stderr = cfg.truncated_output(stderr_b.decode("utf-8", "ignore"))

        return ExecutionResult(
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            backend=self.backend.value,
        )

    async def _kill(self, proc: asyncio.subprocess.Process) -> None:
        try:
            proc.kill()
            await proc.wait()
        except (ProcessLookupError, OSError):
            pass

    async def health(self) -> Dict[str, Any]:
        return {
            "backend": self.backend.value,
            "available": self._docker is not None,
            "isolation": "container",
            "image": self.image,
            "network": "none (default)",
            "security_note": "strong isolation (ephemeral, read-only, no-network)",
        }

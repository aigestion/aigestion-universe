"""Process executor — subprocess isolation with resource limits.

Cross-platform: on Unix applies RLIMIT (CPU, memory) via preexec_fn;
on Windows relies on timeout-kill (memory limits need job objects).
"""
from __future__ import annotations

import asyncio
import os
import platform
import signal
import time
from typing import Any, Dict, Optional

from .base import Backend, ExecutionResult, Executor, SandboxConfig

IS_UNIX = platform.system() != "Windows"

if IS_UNIX:
    import resource  # Unix-only: RLIMIT_CPU / RLIMIT_AS / RLIMIT_CORE


def _apply_rlimits(config: SandboxConfig) -> None:
    """Set RLIMITs in the child process (Unix only)."""
    if not IS_UNIX:
        return
    try:
        # CPU seconds (soft, hard)
        cpu = max(1, int(config.timeout_s))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
        # Address space (bytes)
        mem = config.max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        # Prevent core dumps
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (ValueError, OSError):
        pass


class ProcessExecutor(Executor):
    """Runs commands as a subprocess with limits.

    NOTE: process isolation is NOT a security boundary. Use the
    Docker executor (or a dedicated sandbox VM) for untrusted code.
    """

    backend = Backend.PROCESS

    def __init__(self, default_workdir: Optional[str] = None) -> None:
        self.default_workdir = default_workdir

    async def exec(
        self,
        command: str,
        *,
        config: Optional[SandboxConfig] = None,
    ) -> ExecutionResult:
        cfg = config or SandboxConfig()
        workdir = cfg.workdir or self.default_workdir or os.getcwd()
        start = time.perf_counter()

        env = os.environ.copy()
        env.update(cfg.env)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
                env=env,
                preexec_fn=_apply_rlimits if IS_UNIX else None,
            )
        except Exception as e:
            return ExecutionResult(
                backend=self.backend.value,
                error=f"spawn failed: {type(e).__name__}: {e}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=cfg.timeout_s
            )
        except asyncio.TimeoutError:
            await self._kill(proc)
            return ExecutionResult(
                exit_code=None,
                stdout="",
                stderr="",
                duration_ms=(time.perf_counter() - start) * 1000,
                timed_out=True,
                backend=self.backend.value,
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
            if IS_UNIX:
                proc.send_signal(signal.SIGKILL)
            else:
                proc.kill()
            await proc.wait()
        except (ProcessLookupError, OSError):
            pass

    async def health(self) -> Dict[str, Any]:
        return {
            "backend": self.backend.value,
            "available": True,
            "isolation": "process",
            "unix_rlimits": IS_UNIX,
            "security_note": "not a hard boundary",
        }

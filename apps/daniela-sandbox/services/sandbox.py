"""
Daniela Sandbox — isolated code/shell execution service.

Backs the `run_shell` tool in the tools-gateway. Pluggable
executors (process / docker), resource limits, network
isolation, and a hash-chained audit log.

Run:  uvicorn services.sandbox:create_app --factory --port 8090
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.audit import AuditLog
from services.executors import (
    Backend,
    DockerExecutor,
    ExecutionResult,
    Executor,
    ProcessExecutor,
    SandboxConfig,
)

SANDBOX_PORT = int(os.environ.get("SANDBOX_PORT", "8090"))
DEFAULT_TIMEOUT_S = float(os.environ.get("DEFAULT_TIMEOUT_S", "30"))
DEFAULT_MAX_OUTPUT_BYTES = int(os.environ.get("DEFAULT_MAX_OUTPUT_BYTES", "1048576"))
DEFAULT_MAX_MEMORY_MB = int(os.environ.get("DEFAULT_MAX_MEMORY_MB", "512"))
DEFAULT_NETWORK = os.environ.get("DEFAULT_NETWORK", "none")
DOCKER_IMAGE = os.environ.get("SANDBOX_DOCKER_IMAGE", "python:3.13-slim")
AUDIT_RETENTION = int(os.environ.get("AUDIT_RETENTION", "1000"))


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class SandboxState:
    def __init__(self) -> None:
        self.executors: Dict[Backend, Executor] = {
            Backend.PROCESS: ProcessExecutor(),
            Backend.DOCKER: DockerExecutor(DOCKER_IMAGE),
        }
        self.audit = AuditLog(capacity=AUDIT_RETENTION)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Daniela Sandbox",
        description="Isolated code/shell execution for Daniela OS",
        version="0.1.0",
    )
    # Eager state so it is available even outside the ASGI
    # lifespan (e.g. TestClient without `with`).
    app.state.sandbox = SandboxState()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _register_routes(app)
    return app


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ExecRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=8192)
    backend: Backend = Backend.PROCESS
    timeout_s: float = Field(DEFAULT_TIMEOUT_S, gt=0, le=600)
    max_output_bytes: int = Field(DEFAULT_MAX_OUTPUT_BYTES, gt=0, le=16_777_216)
    max_memory_mb: int = Field(DEFAULT_MAX_MEMORY_MB, gt=0, le=8192)
    network_allowed: bool = False
    workdir: Optional[str] = None
    env: Dict[str, str] = Field(default_factory=dict)


class ExecResponse(BaseModel):
    ok: bool
    backend: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool
    error: Optional[str] = None
    audit_seq: int
    audit_digest: str


class HealthResponse(BaseModel):
    status: str
    executors: Dict[str, Any]


class AuditVerifyResponse(BaseModel):
    valid: bool
    entries: int
    latest_digest: str


class PythonRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=32768)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def _register_routes(app: FastAPI) -> None:
    @app.get("/health", response_model=HealthResponse)
    async def health(request: Request):
        state: SandboxState = request.app.state.sandbox
        executors = {}
        for kind, executor in state.executors.items():
            executors[kind.value] = await executor.health()
        return HealthResponse(status="ok", executors=executors)

    @app.post("/exec", response_model=ExecResponse)
    async def execute(req: ExecRequest, request: Request):
        state: SandboxState = request.app.state.sandbox
        executor = state.executors.get(req.backend)
        if executor is None:
            raise HTTPException(status_code=400, detail=f"unknown backend {req.backend}")

        config = SandboxConfig(
            timeout_s=req.timeout_s,
            max_output_bytes=req.max_output_bytes,
            max_memory_mb=req.max_memory_mb,
            workdir=req.workdir,
            network_allowed=req.network_allowed,
            env=req.env,
        )

        result: ExecutionResult = await executor.exec(req.command, config=config)

        # Redact obvious secrets before audit/return.
        safe_command = _redact(req.command)
        entry = state.audit.record(
            backend=result.backend,
            command=safe_command,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )

        return ExecResponse(
            ok=result.ok,
            backend=result.backend,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=round(result.duration_ms, 3),
            timed_out=result.timed_out,
            error=result.error,
            audit_seq=entry.seq,
            audit_digest=entry.digest,
        )

    @app.post("/python", response_model=ExecResponse)
    async def run_python(body: PythonRequest, request: Request):
        """Execute a Python snippet in the sandbox.

        Writes the snippet to a temp file and executes it, avoiding
        shell-quoting pitfalls (works on both Unix sh and Windows cmd).
        """
        import tempfile
        import sys

        state: SandboxState = request.app.state.sandbox
        executor = state.executors[Backend.PROCESS]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(body.code)
            tmp_path = tmp.name
        try:
            wrapped = f"{sys.executable} {tmp_path}"
            config = SandboxConfig(
                timeout_s=DEFAULT_TIMEOUT_S,
                max_output_bytes=DEFAULT_MAX_OUTPUT_BYTES,
                max_memory_mb=DEFAULT_MAX_MEMORY_MB,
                network_allowed=False,
            )
            result = await executor.exec(wrapped, config=config)
        finally:
            try:
                import os as _os
                _os.unlink(tmp_path)
            except OSError:
                pass
        entry = state.audit.record(
            backend=result.backend,
            command=_redact(wrapped),
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )
        return ExecResponse(
            ok=result.ok,
            backend=result.backend,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=round(result.duration_ms, 3),
            timed_out=result.timed_out,
            error=result.error,
            audit_seq=entry.seq,
            audit_digest=entry.digest,
        )

    @app.get("/audit")
    async def audit(request: Request, limit: int = 100):
        state: SandboxState = request.app.state.sandbox
        return {"entries": state.audit.entries(limit)}

    @app.get("/audit/verify", response_model=AuditVerifyResponse)
    async def audit_verify(request: Request):
        state: SandboxState = request.app.state.sandbox
        return AuditVerifyResponse(
            valid=state.audit.verify(),
            entries=len(state.audit.entries()),
            latest_digest=state.audit.latest_digest(),
        )


def _redact(text: str) -> str:
    """Redact likely secrets before persisting to the audit log."""
    import re
    rules = [
        # (pattern, replacement) — group counts differ per rule
        (r"(?i)(api[_-]?key|token|secret|password)(\s*[:=]\s*)[^\s]+",
         r"\1\2***REDACTED***"),
        (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
         "Bearer ***REDACTED***"),
    ]
    out = text
    for pattern, replacement in rules:
        out = re.sub(pattern, replacement, out)
    return out


def run(host: str = "0.0.0.0", port: int = SANDBOX_PORT) -> None:
    import uvicorn
    uvicorn.run("services.sandbox:create_app", host=host, port=port, factory=True)


if __name__ == "__main__":
    run()

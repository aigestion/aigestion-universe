"""
Daniela Tools Gateway - BYOK tool/MCP unification.

Routes LLM calls and tool invocations to any provider
(OpenAI, Anthropic, Google, local) using the user's own
API keys. Applies ZERO markup on token costs. Exposes both
a REST API and an MCP-compatible JSON-RPC endpoint.

Run:  uvicorn services.tools_gateway:create_app --factory --port 8083
"""
from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

from services.providers import (
    AnthropicProvider,
    GoogleProvider,
    LocalProvider,
    OpenAIProvider,
    Provider,
    ProviderKind,
)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
GATEWAY_PORT = int(os.environ.get("GATEWAY_PORT", "8083"))
ALLOW_MARKUP = os.environ.get("ALLOW_MARKUP", "false").lower() == "true"


def _env_key(name: str) -> Optional[str]:
    value = os.environ.get(name)
    return value if value else None


# ---------------------------------------------------------------------------
# Tool registry (MCP-compatible)
# ---------------------------------------------------------------------------
@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    provider: str = "local"


@dataclass
class UsageRecord:
    id: str
    timestamp: float
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class ToolRegistry:
    """Registry of callable tools, MCP-compatible."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        builtins = [
            ("web_search", "Search the web for current information",
             {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
            ("read_file", "Read the contents of a file",
             {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
            ("write_file", "Write content to a file",
             {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}),
            ("run_shell", "Run a shell command (sandboxed)",
             {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}),
            ("memory_recall", "Recall relevant memories from the vault",
             {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
        ]
        for name, desc, schema in builtins:
            self._tools[name] = Tool(name=name, description=desc, input_schema=schema)

    def register(self, name: str, description: str, input_schema: Dict[str, Any],
                 provider: str = "local") -> Tool:
        tool = Tool(name=name, description=description, input_schema=input_schema, provider=provider)
        self._tools[name] = tool
        return tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list(self) -> List[Tool]:
        return list(self._tools.values())


# ---------------------------------------------------------------------------
# Provider registry (BYOK)
# ---------------------------------------------------------------------------
class ProviderRegistry:
    """Holds configured BYOK providers and routes calls."""

    def __init__(self) -> None:
        self._providers: Dict[ProviderKind, Provider] = {
            ProviderKind.OPENAI: OpenAIProvider(_env_key("OPENAI_API_KEY")),
            ProviderKind.ANTHROPIC: AnthropicProvider(_env_key("ANTHROPIC_API_KEY")),
            ProviderKind.GOOGLE: GoogleProvider(_env_key("GOOGLE_API_KEY")),
            ProviderKind.LOCAL: LocalProvider(),
        }

    def get(self, kind: ProviderKind) -> Optional[Provider]:
        return self._providers.get(kind)

    def all(self) -> Dict[ProviderKind, Provider]:
        return dict(self._providers)

    def available(self) -> List[Provider]:
        return [p for p in self._providers.values() if p.configured]

    async def complete(
        self,
        prompt: str,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ):
        """Route a completion request. Explicit provider wins; else first available."""
        chosen: Optional[Provider] = None
        if provider:
            for kind, p in self._providers.items():
                if kind.value == provider:
                    chosen = p
                    break
            if chosen is None:
                raise ValueError(f"unknown provider: {provider}")
        else:
            avail = self.available()
            if not avail:
                raise RuntimeError("no provider configured (set a BYOK key or run a local LLM)")
            # Prefer local (free) when available, else first configured.
            chosen = next((p for p in avail if p.kind == ProviderKind.LOCAL), avail[0])
        return await chosen.complete(
            prompt, model=model, system=system,
            max_tokens=max_tokens, temperature=temperature,
        )


# ---------------------------------------------------------------------------
# Usage ledger (zero markup)
# ---------------------------------------------------------------------------
class UsageLedger:
    """Append-only ledger of token usage and raw provider cost."""

    def __init__(self) -> None:
        self._records: List[UsageRecord] = []

    def record(self, resp) -> UsageRecord:
        rec = UsageRecord(
            id=str(uuid.uuid4()),
            timestamp=time.time(),
            provider=resp.provider,
            model=resp.model,
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
            cost_usd=resp.cost_usd,
        )
        self._records.append(rec)
        return rec

    def summary(self) -> Dict[str, Any]:
        total_tokens = sum(r.prompt_tokens + r.completion_tokens for r in self._records)
        total_cost = sum(r.cost_usd for r in self._records)
        by_provider: Dict[str, Dict[str, Any]] = {}
        for r in self._records:
            agg = by_provider.setdefault(
                r.provider,
                {"calls": 0, "tokens": 0, "cost_usd": 0.0},
            )
            agg["calls"] += 1
            agg["tokens"] += r.prompt_tokens + r.completion_tokens
            agg["cost_usd"] += r.cost_usd
        return {
            "calls": len(self._records),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "markup_applied": ALLOW_MARKUP,
            "by_provider": by_provider,
        }

    def records(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [
            {
                "id": r.id, "provider": r.provider, "model": r.model,
                "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
                "cost_usd": r.cost_usd, "timestamp": r.timestamp,
            }
            for r in self._records[-limit:]
        ]


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
@dataclass
class GatewayState:
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    providers: ProviderRegistry = field(default_factory=ProviderRegistry)
    usage: UsageLedger = field(default_factory=UsageLedger)


def create_app() -> FastAPI:
    state = GatewayState()

    app = FastAPI(
        title="Daniela Tools Gateway",
        description="BYOK tool/MCP unification - zero markup",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.gateway = state
    _register_routes(app)
    return app


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    prompt: str
    provider: Optional[str] = None
    model: Optional[str] = None
    system: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.7


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}
    provider: Optional[str] = None


class ToolRegisterRequest(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class KeyRequest(BaseModel):
    provider: str
    key: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def _register_routes(app: FastAPI) -> None:
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "tools-gateway", "markup": ALLOW_MARKUP}

    @app.post("/chat/completions")
    async def chat_completions(req: ChatRequest, request: Request):
        state: GatewayState = request.app.state.gateway
        try:
            resp = await state.providers.complete(
                req.prompt,
                provider=req.provider,
                model=req.model,
                system=req.system,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except (httpx.HTTPError, OSError) as e:
            # Provider unreachable (e.g. local LLM server down, network error).
            raise HTTPException(
                status_code=503,
                detail=f"provider unreachable: {type(e).__name__}",
            )
        state.usage.record(resp)
        return {
            "text": resp.text,
            "provider": resp.provider,
            "model": resp.model,
            "usage": {
                "prompt_tokens": resp.prompt_tokens,
                "completion_tokens": resp.completion_tokens,
                "total_tokens": resp.total_tokens,
                "cost_usd": resp.cost_usd,
            },
        }

    @app.get("/providers")
    async def list_providers(request: Request):
        state: GatewayState = request.app.state.gateway
        out = []
        for kind, p in state.providers.all().items():
            out.append({
                "provider": kind.value,
                "configured": p.configured,
            })
        return {"providers": out}

    @app.post("/keys")
    async def set_key(req: KeyRequest, request: Request):
        # In-memory only (production: secret manager / HSM).
        state: GatewayState = request.app.state.gateway
        for kind, p in state.providers.all().items():
            if kind.value == req.provider:
                p.api_key = req.key
                return {"provider": req.provider, "configured": True}
        raise HTTPException(status_code=404, detail="unknown provider")

    @app.get("/tools")
    async def list_tools(request: Request):
        state: GatewayState = request.app.state.gateway
        return {
            "tools": [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in state.tools.list()
            ]
        }

    @app.post("/tools/register")
    async def register_tool(req: ToolRegisterRequest, request: Request):
        state: GatewayState = request.app.state.gateway
        tool = state.tools.register(req.name, req.description, req.input_schema)
        return {"registered": tool.name}

    @app.post("/tools/call")
    async def call_tool(req: ToolCallRequest, request: Request):
        state: GatewayState = request.app.state.gateway
        tool = state.tools.get(req.name)
        if tool is None:
            raise HTTPException(status_code=404, detail="unknown tool")
        # Dispatch to the tool implementation (local by default).
        result = await _execute_tool(tool, req.arguments)
        return {"tool": tool.name, "result": result}

    @app.get("/usage")
    async def usage(request: Request):
        state: GatewayState = request.app.state.gateway
        return state.usage.summary()

    @app.get("/usage/records")
    async def usage_records(request: Request, limit: int = 100):
        state: GatewayState = request.app.state.gateway
        return {"records": state.usage.records(limit)}

    # --- MCP-compatible JSON-RPC endpoint ---
    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """Minimal MCP JSON-RPC: tools/list and tools/call."""
        state: GatewayState = request.app.state.gateway
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if method == "tools/list":
            result = {
                "tools": [
                    {"name": t.name, "description": t.description, "inputSchema": t.input_schema}
                    for t in state.tools.list()
                ]
            }
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            tool = state.tools.get(name)
            if tool is None:
                return {"jsonrpc": "2.0", "id": request_id,
                        "error": {"code": -32602, "message": f"unknown tool {name}"}}
            result = {"content": [{"type": "text", "text": str(await _execute_tool(tool, arguments))}]}
        else:
            return {"jsonrpc": "2.0", "id": request_id,
                    "error": {"code": -32601, "message": f"method not found: {method}"}}

        return {"jsonrpc": "2.0", "id": request_id, "result": result}


async def _execute_tool(tool: Tool, arguments: Dict[str, Any]) -> Any:
    """Execute a registered tool. Built-ins are simulated; custom tools route out."""
    if tool.name == "memory_recall":
        return {"query": arguments.get("query"), "results": []}
    if tool.name == "web_search":
        return {"query": arguments.get("query"), "results": []}
    return {"tool": tool.name, "arguments": arguments, "executed": False,
            "note": "tool executor not wired in this scaffold"}


def run(host: str = "0.0.0.0", port: int = GATEWAY_PORT) -> None:
    import uvicorn
    uvicorn.run("services.tools_gateway:create_app", host=host, port=port, factory=True)


if __name__ == "__main__":
    run()

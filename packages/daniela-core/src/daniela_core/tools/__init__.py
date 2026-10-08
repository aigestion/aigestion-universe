"""
Tool Gateway - BYOK tool unification with zero markup.

Routes LLM calls to any provider (OpenAI, Anthropic, Google, local)
using the user's own API keys. Compatible with the MCP tool protocol.
Never marks up token costs.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class UnknownToolError(KeyError):
    """Unknown tool name."""

    def __init__(self, name: str) -> None:
        super().__init__(f"unknown tool {name}")


class Provider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    provider: Provider = Provider.LOCAL


@dataclass
class ToolResult:
    tool_call_id: str
    output: Any
    tokens_used: int = 0
    cost_usd: float = 0.0


class ToolGateway:
    """Unified tool/MCP gateway. BYOK, zero markup."""

    def __init__(self) -> None:
        self.tools: dict[str, dict[str, Any]] = {}
        self._keys: dict[Provider, str] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._initialized = True
        self._register_builtin_tools()

    async def shutdown(self) -> None:
        async with self._lock:
            self.tools.clear()
            self._keys.clear()

    def set_key(self, provider: Provider, key: str) -> None:
        """Store a provider key in memory (production: secret manager/HSM)."""
        self._keys[provider] = key

    def has_key(self, provider: Provider) -> bool:
        return provider in self._keys

    def _register_builtin_tools(self) -> None:
        builtin = {
            "web_search": {"description": "Search the web", "input": {"query": "string"}},
            "read_file": {"description": "Read a file", "input": {"path": "string"}},
            "write_file": {
                "description": "Write a file",
                "input": {"path": "string", "content": "string"},
            },
            "run_shell": {"description": "Run a shell command", "input": {"cmd": "string"}},
            "memory_recall": {"description": "Recall memories", "input": {"query": "string"}},
        }
        self.tools.update(builtin)

    async def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
    ) -> None:
        async with self._lock:
            self.tools[name] = {"description": description, "input": input_schema}

    async def call(
        self,
        name: str,
        *,
        arguments: dict[str, Any] | None = None,
        provider: Provider = Provider.LOCAL,
    ) -> ToolResult:
        if name not in self.tools:
            raise UnknownToolError(name)
        call = ToolCall(
            id=str(uuid.uuid4()),
            name=name,
            arguments=arguments or {},
            provider=provider,
        )
        output = await self._execute(call)
        return ToolResult(tool_call_id=call.id, output=output, tokens_used=0, cost_usd=0.0)

    async def _execute(self, call: ToolCall) -> Any:
        # Production: route to provider via HTTP with the stored BYOK key.
        # Local tools execute deterministically here.
        if call.name == "memory_recall":
            return {"query": call.arguments.get("query"), "results": []}
        return {"tool": call.name, "arguments": call.arguments, "provider": call.provider.value}

    def list_tools(self) -> dict[str, Any]:
        return dict(self.tools)

    def providers(self) -> dict[str, bool]:
        return {p.value: self.has_key(p) for p in Provider}

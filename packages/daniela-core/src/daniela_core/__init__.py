"""Daniela Core - Autonomous AI Service Management & Edge Orchestrator.

Minimal root: submodules are imported on demand (PEP 562) so a broken
optional/legacy module never prevents `import daniela_core`.
"""

from __future__ import annotations

import importlib
from typing import Any

__version__ = "0.1.0"

_LAZY: dict[str, str] = {
    "Brain": "daniela_core.brain",
    "MemoryVault": "daniela_core.memory",
    "MemoryTier": "daniela_core.memory",
    "Orchestrator": "daniela_core.orchestrator",
    "Engine": "daniela_core.orchestrator",
    "TaskStatus": "daniela_core.orchestrator",
    "PersonaManager": "daniela_core.persona",
    "DigitalLife": "daniela_core.life",
    "SecurityEngine": "daniela_core.security",
    "VoiceEngine": "daniela_core.voice",
    "AgentRegistry": "daniela_core.agents",
    "AgentRole": "daniela_core.agents",
    "Agent": "daniela_core.agents",
    "ToolGateway": "daniela_core.tools",
    "Provider": "daniela_core.tools",
    "ToolCall": "daniela_core.tools",
    "ToolResult": "daniela_core.tools",
    "Event": "daniela_core.events",
    "Command": "daniela_core.events",
    "NATSEventBus": "daniela_core.events",
    "ServiceRegistry": "daniela_core.registry",
}

__all__ = [
    "Agent",
    "AgentRegistry",
    "AgentRole",
    "Brain",
    "Command",
    "DigitalLife",
    "Engine",
    "Event",
    "MemoryTier",
    "MemoryVault",
    "NATSEventBus",
    "Orchestrator",
    "PersonaManager",
    "Provider",
    "SecurityEngine",
    "ServiceRegistry",
    "TaskStatus",
    "ToolCall",
    "ToolGateway",
    "ToolResult",
    "VoiceEngine",
    "__version__",
]


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        module = importlib.import_module(_LAZY[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)

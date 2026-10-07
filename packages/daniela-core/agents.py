"""
Agent Registry - Sub-agent swarm for Daniela.

Specialized agents (planner, coder, reviewer, researcher) register
themselves and are dispatched by the Orchestrator.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AgentRole(StrEnum):
    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    TESTER = "tester"
    DEPLOYER = "deployer"


@dataclass
class Agent:
    id: str
    name: str
    role: AgentRole
    capabilities: list[str] = field(default_factory=list)
    busy: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "busy": self.busy,
        }


class AgentRegistry:
    """Registry and dispatcher for the sub-agent swarm."""

    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._initialized = True
        defaults = [
            ("Atlas", AgentRole.PLANNER, ["decompose", "plan"]),
            ("Vega", AgentRole.CODER, ["write", "edit", "refactor"]),
            ("Sentinel", AgentRole.REVIEWER, ["security", "style", "performance"]),
            ("Sage", AgentRole.RESEARCHER, ["search", "summarize"]),
            ("Probe", AgentRole.TESTER, ["unit", "integration", "e2e"]),
            ("Harbor", AgentRole.DEPLOYER, ["docker", "compose", "k3s"]),
        ]
        for name, role, caps in defaults:
            agent = Agent(id=str(uuid.uuid4()), name=name, role=role, capabilities=caps)
            self.agents[agent.id] = agent

    async def shutdown(self) -> None:
        async with self._lock:
            self.agents.clear()

    async def register(
        self, name: str, role: AgentRole, capabilities: list[str] | None = None
    ) -> Agent:
        async with self._lock:
            agent = Agent(
                id=str(uuid.uuid4()),
                name=name,
                role=role,
                capabilities=capabilities or [],
            )
            self.agents[agent.id] = agent
            return agent

    async def dispatch(self, role: AgentRole) -> Agent | None:
        """Find a free agent with the requested role."""
        async with self._lock:
            for agent in self.agents.values():
                if agent.role == role and not agent.busy:
                    agent.busy = True
                    return agent
            return None

    async def release(self, agent_id: str) -> None:
        async with self._lock:
            agent = self.agents.get(agent_id)
            if agent:
                agent.busy = False

    def list(self) -> list[dict[str, Any]]:
        return [a.as_dict() for a in self.agents.values()]

"""Agents package - registry + role definitions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import builtins
from enum import StrEnum

from .agents import AGENTS


class AgentRole(StrEnum):
    """Roles for the managed agent pool."""

    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    TESTER = "tester"
    DEPLOYER = "deployer"


@dataclass
class Agent:
    """A managed agent instance."""

    id: str
    name: str
    role: AgentRole
    capabilities: list[str] = field(default_factory=list)
    busy: bool = False

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "busy": self.busy,
        }


_DEFAULT_CAPABILITIES: dict[AgentRole, builtins.list[str]] = {
    AgentRole.PLANNER: ["decompose", "plan"],
    AgentRole.CODER: ["write", "edit", "refactor"],
    AgentRole.REVIEWER: ["security", "style", "performance"],
    AgentRole.RESEARCHER: ["search", "summarize"],
    AgentRole.TESTER: ["unit", "integration", "e2e"],
    AgentRole.DEPLOYER: ["docker", "compose", "k3s"],
}


class AgentRegistry:
    """Registry + dispatcher for the managed agent pool."""

    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {}
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        for role in AgentRole:
            agent = Agent(
                id=str(uuid.uuid4()),
                name=f"{role.value}-{role.value}",
                role=role,
                capabilities=list(_DEFAULT_CAPABILITIES.get(role, [])),
            )
            self.agents[agent.id] = agent
        self._initialized = True

    async def shutdown(self) -> None:
        self.agents.clear()
        self._initialized = False

    def list(self) -> builtins.list[dict]:
        return [a.as_dict() for a in self.agents.values()]

    async def dispatch(self, role: AgentRole) -> Agent | None:
        """Return a free agent of the role, marked busy (None if exhausted)."""
        for agent in self.agents.values():
            if agent.role == role and not agent.busy:
                agent.busy = True
                return agent
        return None

    async def register(
        self, name: str, role: AgentRole, capabilities: builtins.list[str] | None = None
    ) -> Agent:
        """Register a new agent and return it."""
        agent = Agent(
            id=str(uuid.uuid4()),
            name=name,
            role=role,
            capabilities=list(capabilities or []),
        )
        self.agents[agent.id] = agent
        return agent

    async def release(self, agent_id: str) -> None:
        agent = self.agents.get(agent_id)
        if agent:
            agent.busy = False


__all__ = [
    "AGENTS",
    "Agent",
    "AgentRegistry",
    "AgentRole",
]

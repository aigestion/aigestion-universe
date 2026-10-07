"""
Orchestrator - Swarm intelligence, Raft consensus, cross-engine gateway.

Coordinates the 19 federated engines: delegates tasks, reaches consensus
via a simplified Raft protocol, and routes through the cross-engine gateway.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Engine(str, Enum):
    CORE = "core"
    DATA_SECURITY = "data_security"
    PERFORMANCE = "performance"
    EXPERIENCE = "experience"
    AUTOMATION = "automation"
    INTEL = "intel"
    AUTO = "auto"
    DATA = "data"
    SECURE = "secure"
    DEVTOOLS = "devtools"
    ECOSYSTEM = "ecosystem"
    UX = "ux"
    SCALE = "scale"
    CHAOS = "chaos"
    BRAND = "brand"
    GATEWAY = "gateway"
    ORCHESTRATOR = "orchchestrator"
    INFRA_OPT = "infra_opt"
    AGENT_MOBILE = "agent_mobile"


class TaskStatus(str, Enum):
    PENDING = "pending"
    DELEGATED = "delegated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    description: str
    engine: Engine | None = None
    status: TaskStatus = TaskStatus.PENDING
    payload: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EngineNode:
    engine: Engine
    endpoint: str
    healthy: bool = True
    load: float = 0.0


class Orchestrator:
    """Swarm orchestrator with Raft-style consensus and cross-engine routing."""

    def __init__(self) -> None:
        self.nodes: dict[Engine, EngineNode] = {}
        self.tasks: dict[str, Task] = {}
        self._term = 0
        self._leader: Engine | None = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._initialized = True
        for engine in Engine:
            self.nodes[engine] = EngineNode(engine=engine, endpoint=f"http://{engine.value}:9900")
        self._leader = Engine.CORE
        self._term = 1

    async def shutdown(self) -> None:
        async with self._lock:
            self.tasks.clear()

    async def delegate(self, description: str, *, payload: dict[str, Any] | None = None) -> Task:
        """Decompose and delegate a task to the best-fit engine."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            task = Task(
                id=str(uuid.uuid4()),
                description=description,
                payload=payload or {},
            )
            task.engine = self._select_engine(description)
            task.status = TaskStatus.DELEGATED
            self.tasks[task.id] = task
            return task

    async def execute(self, task_id: str) -> dict[str, Any]:
        """Execute a delegated task (simulated engine call)."""
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                raise KeyError(f"unknown task {task_id}")
            task.status = TaskStatus.RUNNING
        # In production this is an HTTP/gRPC call to the engine endpoint.
        await asyncio.sleep(0)
        async with self._lock:
            task.result = {"engine": task.engine.value, "echo": task.description}
            task.status = TaskStatus.COMPLETED
            return task.result or {}

    async def consensus(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """Raft-style consensus: leader proposes, majority of nodes accept."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            self._term += 1
            healthy = [n for n in self.nodes.values() if n.healthy]
            quorum = len(healthy) // 2 + 1
            votes = sum(1 for n in healthy if self._vote(n, proposal))
            accepted = votes >= quorum
            return {
                "term": self._term,
                "leader": self._leader.value if self._leader else None,
                "votes": votes,
                "quorum": quorum,
                "accepted": accepted,
            }

    def _select_engine(self, description: str) -> Engine:
        """Heuristic keyword routing to the best-fit engine."""
        d = description.lower()
        if any(k in d for k in ("security", "encrypt", "vault", "token")):
            return Engine.SECURE
        if any(k in d for k in ("mobile", "android", "pixel", "termux")):
            return Engine.AGENT_MOBILE
        if any(k in d for k in ("design", "brand", "logo", "color")):
            return Engine.BRAND
        if any(k in d for k in ("performance", "latency", "benchmark")):
            return Engine.PERFORMANCE
        if any(k in d for k in ("deploy", "docker", "k8s", "k3s")):
            return Engine.AUTOMATION
        return Engine.CORE

    @staticmethod
    def _vote(node: EngineNode, proposal: dict[str, Any]) -> bool:
        return node.healthy and node.load < 0.95

    def stats(self) -> dict[str, Any]:
        return {
            "term": self._term,
            "leader": self._leader.value if self._leader else None,
            "nodes": len(self.nodes),
            "healthy": sum(1 for n in self.nodes.values() if n.healthy),
            "tasks": len(self.tasks),
        }

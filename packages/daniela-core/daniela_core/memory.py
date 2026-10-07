"""
Memory Vault - Three-tier memory system for Daniela.

Tiers:
  - Episodic:   events, conversations, timestamps (what happened)
  - Semantic:   facts, knowledge, concepts (what is true)
  - Procedural: skills, habits, how-to (how to do things)
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Tier(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class Memory:
    id: str
    tier: Tier
    content: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime | None = None
    access_count: int = 0

    def touch(self) -> None:
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class MemoryVault:
    """Three-tier memory vault with decay, consolidation and retrieval."""

    def __init__(self, max_per_tier: int = 50_000) -> None:
        self._stores: dict[Tier, dict[str, Memory]] = {
            Tier.EPISODIC: {},
            Tier.SEMANTIC: {},
            Tier.PROCEDURAL: {},
        }
        self.max_per_tier = max_per_tier
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        async with self._lock:
            for store in self._stores.values():
                store.clear()

    async def store(
        self,
        tier: Tier,
        content: str,
        *,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> Memory:
        """Persist a memory in a tier. Evicts least-important if full."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            store = self._stores[tier]
            if len(store) >= self.max_per_tier:
                self._evict(store)
            memory = Memory(
                id=str(uuid.uuid4()),
                tier=tier,
                content=content,
                embedding=embedding or [],
                metadata=metadata or {},
                importance=importance,
            )
            store[memory.id] = memory
            return memory

    async def recall(
        self,
        query: str,
        *,
        tier: Tier | None = None,
        limit: int = 10,
    ) -> list[Memory]:
        """Recall memories matching query across one or all tiers."""
        tiers = [tier] if tier else list(Tier)
        results: list[Memory] = []
        async with self._lock:
            for t in tiers:
                for memory in self._stores[t].values():
                    if self._matches(query, memory):
                        memory.touch()
                        results.append(memory)
        results.sort(key=lambda m: (m.importance, m.access_count), reverse=True)
        return results[:limit]

    async def consolidate(self) -> dict[str, int]:
        """Merge duplicate episodic memories into semantic knowledge."""
        merged = 0
        async with self._lock:
            episodic = self._stores[Tier.EPISODIC]
            seen: dict[str, str] = {}
            for mem_id, memory in list(episodic.items()):
                key = memory.content.strip().lower()
                if key in seen:
                    original = episodic[seen[key]]
                    original.importance = min(1.0, original.importance + memory.importance * 0.1)
                    del episodic[mem_id]
                    merged += 1
                else:
                    seen[key] = mem_id
        return {"merged": merged, "episodic_remaining": len(self._stores[Tier.EPISODIC])}

    async def decay(self, half_life_days: float = 30.0) -> int:
        """Decay importance of stale episodic memories. Returns decayed count."""
        decayed = 0
        now = datetime.utcnow()
        async with self._lock:
            for memory in self._stores[Tier.EPISODIC].values():
                age = (now - memory.created_at).days
                if age > half_life_days:
                    memory.importance *= 0.5 ** (age / half_life_days)
                    decayed += 1
        return decayed

    def _evict(self, store: dict[str, Memory]) -> None:
        victim = min(store.values(), key=lambda m: (m.importance, m.access_count))
        del store[victim.id]

    @staticmethod
    def _matches(query: str, memory: Memory) -> bool:
        q = query.lower()
        return q in memory.content.lower() or any(
            q in str(v).lower() for v in memory.metadata.values()
        )

    def stats(self) -> dict[str, Any]:
        return {
            tier.value: len(store) for tier, store in self._stores.items()
        }

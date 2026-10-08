"""
CRDT (Conflict-free Replicated Data Types) for aig.

Provides automatic conflict resolution for offline-first sync
using vector clocks and last-write-wins semantics.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MergeStrategy(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "lww"
    FIRST_WRITE_WINS = "fww"
    MERGE = "merge"
    CUSTOM = "custom"


@dataclass
class VectorClock:
    """Vector clock for tracking causality across nodes."""
    clocks: dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str) -> None:
        """Increment clock for a node."""
        self.clocks[node_id] = self.clocks.get(node_id, 0) + 1

    def merge(self, other: VectorClock) -> VectorClock:
        """Merge two vector clocks."""
        merged = {}
        for node in set(self.clocks) | set(other.clocks):
            merged[node] = max(
                self.clocks.get(node, 0),
                other.clocks.get(node, 0)
            )
        return VectorClock(merged)

    def happens_before(self, other: VectorClock) -> bool:
        """Check if self happens before other (causality)."""
        for node, clock in self.clocks.items():
            if clock > other.clocks.get(node, 0):
                return False
        return any(
            self.clocks.get(node, 0) < other.clocks.get(node, 0)
            for node in other.clocks
        )

    def is_concurrent(self, other: VectorClock) -> bool:
        """Check if two clocks are concurrent (no causality)."""
        return not self.happens_before(other) and not other.happens_before(self)

    def is_equal(self, other: VectorClock) -> bool:
        """Check if two clocks are equal."""
        return self.clocks == other.clocks


@dataclass
class CRDTValue:
    """Last-Write-Wins register with vector clock."""
    value: Any
    timestamp: float
    node_id: str
    vector_clock: VectorClock = field(default_factory=VectorClock)
    deleted: bool = False

    def merge(self, other: CRDTValue) -> CRDTValue:
        """Merge two CRDT values."""
        # Check causality
        if self.vector_clock.happens_before(other.vector_clock):
            return other
        if other.vector_clock.happens_before(self.vector_clock):
            return self

        # Concurrent updates - use timestamp tiebreaker
        if self.timestamp != other.timestamp:
            winner = self if self.timestamp > other.timestamp else other
        else:
            # Same timestamp - use node_id for deterministic ordering
            winner = self if self.node_id > other.node_id else other

        return CRDTValue(
            value=winner.value,
            timestamp=max(self.timestamp, other.timestamp),
            node_id=winner.node_id,
            vector_clock=self.vector_clock.merge(other.vector_clock),
            deleted=winner.deleted,
        )

    def increment_clock(self) -> None:
        """Increment this node's clock."""
        self.vector_clock.increment(self.node_id)


@dataclass
class CRDTMap:
    """CRDT map (dictionary) with per-key conflict resolution."""
    entries: dict[str, CRDTValue] = field(default_factory=dict)
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def set(self, key: str, value: Any, timestamp: float | None = None) -> None:
        """Set a key in the map."""
        ts = timestamp or time.time()
        self.entries[key] = CRDTValue(
            value=value,
            timestamp=ts,
            node_id=self.node_id,
            vector_clock=VectorClock({self.node_id: len(self.entries) + 1}),
        )

    def get(self, key: str) -> Any | None:
        """Get a key's value."""
        entry = self.entries.get(key)
        if entry and not entry.deleted:
            return entry.value
        return None

    def delete(self, key: str) -> None:
        """Soft-delete a key (tombstone)."""
        if key in self.entries:
            self.entries[key].deleted = True
            self.entries[key].timestamp = time.time()

    def merge(self, other: CRDTMap) -> CRDTMap:
        """Merge two CRDT maps."""
        merged = CRDTMap(node_id=self.node_id)

        # Merge all keys from both maps
        all_keys = set(self.entries) | set(other.entries)
        for key in all_keys:
            self_entry = self.entries.get(key)
            other_entry = other.entries.get(key)

            if self_entry and other_entry:
                merged.entries[key] = self_entry.merge(other_entry)
            elif self_entry:
                merged.entries[key] = self_entry
            elif other_entry:
                merged.entries[key] = other_entry

        return merged

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dictionary (excluding deleted)."""
        return {
            key: entry.value
            for key, entry in self.entries.items()
            if not entry.deleted
        }


class CRDTSet:
    """CRDT set with add/remove semantics."""

    def __init__(self, node_id: str | None = None):
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.adds: dict[str, CRDTValue] = {}
        self.removes: dict[str, CRDTValue] = {}

    def add(self, element: str) -> None:
        """Add an element to the set."""
        self.adds[element] = CRDTValue(
            value=element,
            timestamp=time.time(),
            node_id=self.node_id,
        )

    def remove(self, element: str) -> None:
        """Remove an element from the set."""
        if element in self.adds:
            self.removes[element] = CRDTValue(
                value=element,
                timestamp=time.time(),
                node_id=self.node_id,
            )

    def contains(self, element: str) -> bool:
        """Check if element is in the set."""
        added = element in self.adds
        removed = element in self.removes

        if added and not removed:
            return True
        if removed and not added:
            return False
        if added and removed:
            # Compare timestamps
            return self.adds[element].timestamp > self.removes[element].timestamp
        return False

    def merge(self, other: CRDTSet) -> CRDTSet:
        """Merge two CRDT sets."""
        merged = CRDTSet(node_id=self.node_id)

        # Merge adds
        all_adds = set(self.adds) | set(other.adds)
        for element in all_adds:
            self_add = self.adds.get(element)
            other_add = other.adds.get(element)
            if self_add and other_add:
                merged.adds[element] = self_add.merge(other_add)
            elif self_add:
                merged.adds[element] = self_add
            elif other_add:
                merged.adds[element] = other_add

        # Merge removes
        all_removes = set(self.removes) | set(other.removes)
        for element in all_removes:
            self_remove = self.removes.get(element)
            other_remove = other.removes.get(element)
            if self_remove and other_remove:
                merged.removes[element] = self_remove.merge(other_remove)
            elif self_remove:
                merged.removes[element] = self_remove
            elif other_remove:
                merged.removes[element] = other_remove

        return merged

    def to_set(self) -> set[str]:
        """Convert to Python set."""
        return {e for e in self.adds if self.contains(e)}


class CRDTCounter:
    """CRDT counter (grow-only with increments/decrements)."""

    def __init__(self, node_id: str | None = None):
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.increments: dict[str, int] = {}
        self.decrements: dict[str, int] = {}

    def increment(self, delta: int = 1) -> None:
        """Increment the counter."""
        self.increments[self.node_id] = self.increments.get(self.node_id, 0) + delta

    def decrement(self, delta: int = 1) -> None:
        """Decrement the counter."""
        self.decrements[self.node_id] = self.decrements.get(self.node_id, 0) + delta

    def value(self) -> int:
        """Get current counter value."""
        total_inc = sum(self.increments.values())
        total_dec = sum(self.decrements.values())
        return total_inc - total_dec

    def merge(self, other: CRDTCounter) -> CRDTCounter:
        """Merge two CRDT counters."""
        merged = CRDTCounter(node_id=self.node_id)

        # Merge increments (take max per node)
        all_nodes = set(self.increments) | set(other.increments)
        for node in all_nodes:
            merged.increments[node] = max(
                self.increments.get(node, 0),
                other.increments.get(node, 0)
            )

        # Merge decrements (take max per node)
        all_nodes = set(self.decrements) | set(other.decrements)
        for node in all_nodes:
            merged.decrements[node] = max(
                self.decrements.get(node, 0),
                other.decrements.get(node, 0)
            )

        return merged


# ─── Conflict Resolver ───

class ConflictResolver:
    """High-level conflict resolver for offline-first sync."""

    def __init__(self, node_id: str | None = None):
        self.node_id = node_id or str(uuid.uuid4())[:8]

    def resolve(self, local: dict, remote: dict) -> dict:
        """Resolve conflict between local and remote documents."""
        merged = CRDTMap(node_id=self.node_id)

        # Convert both to CRDT maps
        local_map = self._to_crdt_map(local)
        remote_map = self._to_crdt_map(remote)

        # Merge
        merged = local_map.merge(remote_map)

        return merged.to_dict()

    def _to_crdt_map(self, data: dict) -> CRDTMap:
        """Convert plain dict to CRDT map."""
        crdt_map = CRDTMap(node_id=self.node_id)
        for key, value in data.items():
            if value is not None:
                crdt_map.set(key, value)
        return crdt_map

    def resolve_field(
        self,
        local_value: Any,
        remote_value: Any,
        strategy: MergeStrategy = MergeStrategy.LAST_WRITE_WINS,
    ) -> Any:
        """Resolve conflict for a single field."""
        if local_value == remote_value:
            return local_value

        if strategy == MergeStrategy.LAST_WRITE_WINS:
            # Assume values have _timestamp metadata
            local_ts = getattr(local_value, "_timestamp", 0)
            remote_ts = getattr(remote_value, "_timestamp", 0)
            return local_value if local_ts >= remote_ts else remote_value

        if strategy == MergeStrategy.MERGE:
            if isinstance(local_value, dict) and isinstance(remote_value, dict):
                return self.resolve(local_value, remote_value)
            if isinstance(local_value, list) and isinstance(remote_value, list):
                return list(set(local_value) | set(remote_value))

        # Default: local wins
        return local_value


# ─── Global Instance ───

_global_resolver: ConflictResolver | None = None


def get_conflict_resolver() -> ConflictResolver:
    """Get or create global conflict resolver."""
    global _global_resolver
    if _global_resolver is None:
        _global_resolver = ConflictResolver()
    return _global_resolver

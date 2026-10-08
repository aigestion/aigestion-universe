"""
Caching (Ideas 1-10)
--------------------
Multi-tier caching, warming, invalidation, stampede prevention, precomputation,
compression, metrics, distributed cache, cache-aside, write-through/write-behind.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Idea 8 - Consistent hashing ring
# ---------------------------------------------------------------------------

class ConsistentHashRing:
    """Distributed cache node routing via consistent hashing."""

    def __init__(self, nodes: list[str], virtual_nodes: int = 150):
        self.ring: dict[int, str] = {}
        self.nodes = set(nodes)
        self.virtual_nodes = virtual_nodes
        self._build_ring()

    def _hash(self, key: str) -> int:
        return int(hashlib.sha256(key.encode()).hexdigest(), 16)

    def _build_ring(self):
        for node in self.nodes:
            for i in range(self.virtual_nodes):
                h = self._hash(f"{node}:v{i}")
                self.ring[h] = node

    def get_node(self, key: str) -> str:
        if not self.ring:
            raise RuntimeError("Empty hash ring")
        h = self._hash(key)
        sorted_keys = sorted(self.ring)
        for sk in sorted_keys:
            if h <= sk:
                return self.ring[sk]
        return self.ring[sorted_keys[0]]

    def add_node(self, node: str):
        self.nodes.add(node)
        for i in range(self.virtual_nodes):
            h = self._hash(f"{node}:v{i}")
            self.ring[h] = node

    def remove_node(self, node: str):
        self.nodes.discard(node)
        self.ring = {k: v for k, v in self.ring.items() if v != node}


# ---------------------------------------------------------------------------
# Idea 2 - Cache warming strategies
# ---------------------------------------------------------------------------

class WarmingStrategy(Enum):
    EAGER = "eager"
    LAZY = "lazy"
    SCHEDULED = "scheduled"
    PREDICTIVE = "predictive"


class CacheWarmer:
    """Warm caches using configurable strategies."""

    def __init__(self, strategy: WarmingStrategy = WarmingStrategy.EAGER):
        self.strategy = strategy
        self._warming_tasks: dict[str, Callable] = {}
        self._warmed_keys: set[str] = set()

    def register(self, key: str, loader: Callable):
        self._warming_tasks[key] = loader

    def warm(self, cache: MultiTierCache, keys: list[str] | None = None):
        targets = keys or list(self._warming_tasks.keys())
        for key in targets:
            if key in self._warming_tasks:
                try:
                    value = self._warming_tasks[key]()
                    cache.set(key, value)
                    self._warmed_keys.add(key)
                except Exception as exc:
                    logger.warning("Cache warming failed for %s: %s", key, exc)

    @property
    def warmed_count(self) -> int:
        return len(self._warmed_keys)


# ---------------------------------------------------------------------------
# Idea 1 - Multi-tier cache (L1 memory, L2 Redis-like, L3 CDN-like)
# ---------------------------------------------------------------------------

@dataclass
class CacheEntry:
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: float = 300.0
    access_count: int = 0

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl


class TieredStore:
    """Single tier store (memory, Redis-sim, or CDN-sim)."""

    def __init__(self, name: str, max_size: int = 1000, default_ttl: float = 300):
        self.name = name
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._data: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None or entry.is_expired:
                if entry is not None:
                    del self._data[key]
                self.misses += 1
                return None
            entry.access_count += 1
            self._data.move_to_end(key)
            self.hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = CacheEntry(value=value, ttl=ttl or self.default_ttl)
            while len(self._data) > self.max_size:
                self._data.popitem(last=False)
                self.evictions += 1

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def clear(self):
        with self._lock:
            self._data.clear()

    @property
    def size(self) -> int:
        return len(self._data)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "size": self.size,
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(self.hit_rate, 4),
        }


# ---------------------------------------------------------------------------
# Idea 4 - Cache stampede prevention
# ---------------------------------------------------------------------------

class StampedePreventer:
    """Prevent cache stampede via single-flight pattern."""

    def __init__(self):
        self._inflight: dict[str, threading.Event] = {}
        self._results: dict[str, Any] = {}
        self._lock = threading.Lock()

    def do_once(self, key: str, loader: Callable) -> Any:
        with self._lock:
            if key in self._results:
                return self._results[key]
            if key in self._inflight:
                # Another thread is already computing; wait for it
                event = self._inflight[key]
                is_owner = False
            else:
                event = threading.Event()
                self._inflight[key] = event
                is_owner = True

        if not is_owner:
            event.wait()
            with self._lock:
                return self._results.get(key)

        # Only the owner thread reaches here
        try:
            value = loader()
            with self._lock:
                self._results[key] = value
                event.set()
                self._inflight.pop(key, None)
            return value
        except Exception:
            with self._lock:
                self._inflight.pop(key, None)
                event.set()
            raise


# ---------------------------------------------------------------------------
# Idea 3 - Cache invalidation patterns
# ---------------------------------------------------------------------------

class InvalidationStrategy(Enum):
    TTL = "ttl"
    EVENT_DRIVEN = "event_driven"
    MANUAL = "manual"


class CacheInvalidator:
    """Event-driven + TTL invalidation."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._invalidation_log: list[tuple[float, str]] = []

    def subscribe(self, event: str, callback: Callable):
        self._subscribers.setdefault(event, []).append(callback)

    def invalidate(self, event: str, keys: list[str] | None = None):
        ts = time.time()
        targets = keys or []
        for k in targets:
            self._invalidation_log.append((ts, k))
        for cb in self._subscribers.get(event, []):
            try:
                cb(targets)
            except Exception as exc:
                logger.warning("Invalidation callback error: %s", exc)

    @property
    def log_count(self) -> int:
        return len(self._invalidation_log)


# ---------------------------------------------------------------------------
# Idea 5 - Cache precomputation
# ---------------------------------------------------------------------------

class PrecomputeManager:
    """Schedule precomputation of expensive results."""

    def __init__(self):
        self._registry: dict[str, Callable] = {}
        self._results: dict[str, Any] = {}
        self._executor = ThreadPoolExecutor(max_workers=2)

    def register(self, key: str, fn: Callable):
        self._registry[key] = fn

    def precompute(self, keys: list[str] | None = None):
        targets = keys or list(self._registry.keys())
        futures = {}
        for k in targets:
            if k in self._registry:
                futures[k] = self._executor.submit(self._registry[k])
        for k, fut in futures.items():
            try:
                self._results[k] = fut.result(timeout=30)
            except Exception as exc:
                logger.warning("Precompute failed for %s: %s", k, exc)

    def get(self, key: str) -> Any | None:
        return self._results.get(key)


# ---------------------------------------------------------------------------
# Idea 6 - Cache compression
# ---------------------------------------------------------------------------

class CacheCompressor:
    """Compress/decompress cached values to save memory."""

    def __init__(self, use_json_compact: bool = True):
        self.use_json_compact = use_json_compact

    def compress(self, value: Any) -> bytes:
        raw = json.dumps(value, separators=(",", ":")) if self.use_json_compact else json.dumps(value)
        return raw.encode("utf-8")

    def decompress(self, data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))

    @staticmethod
    def estimate_savings(value: Any) -> dict[str, int]:
        full = len(json.dumps(value))
        compact = len(json.dumps(value, separators=(",", ":")))
        return {"original": full, "compressed": compact, "saved": full - compact}


# ---------------------------------------------------------------------------
# Idea 7 - Cache metrics
# ---------------------------------------------------------------------------

@dataclass
class CacheMetrics:
    """Aggregate metrics across tiers."""

    total_hits: int = 0
    total_misses: int = 0
    total_sets: int = 0
    total_evictions: int = 0
    avg_latency_us: float = 0.0
    _latencies: list[float] = field(default_factory=list)

    def record_hit(self):
        self.total_hits += 1

    def record_miss(self):
        self.total_misses += 1

    def record_set(self):
        self.total_sets += 1

    def record_latency(self, us: float):
        self._latencies.append(us)
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-500:]
        self.avg_latency_us = sum(self._latencies) / len(self._latencies)

    @property
    def hit_rate(self) -> float:
        total = self.total_hits + self.total_misses
        return self.total_hits / total if total > 0 else 0.0

    def report(self) -> dict[str, Any]:
        return {
            "hits": self.total_hits,
            "misses": self.total_misses,
            "sets": self.total_sets,
            "evictions": self.total_evictions,
            "hit_rate": round(self.hit_rate, 4),
            "avg_latency_us": round(self.avg_latency_us, 2),
        }


# ---------------------------------------------------------------------------
# Idea 9 - Cache-aside pattern
# ---------------------------------------------------------------------------

class CacheAside:
    """Cache-aside (lazy loading) pattern implementation."""

    def __init__(self, store: TieredStore):
        self.store = store
        self.metrics = CacheMetrics()

    def get_or_load(self, key: str, loader: Callable, ttl: float | None = None) -> Any:
        start = time.monotonic()
        value = self.store.get(key)
        elapsed = (time.monotonic() - start) * 1_000_000
        self.metrics.record_latency(elapsed)

        if value is not None:
            self.metrics.record_hit()
            return value

        self.metrics.record_miss()
        value = loader()
        self.store.set(key, value, ttl=ttl)
        self.metrics.record_set()
        return value

    def invalidate(self, key: str):
        self.store.delete(key)


# ---------------------------------------------------------------------------
# Idea 10 - Write-through / Write-behind cache
# ---------------------------------------------------------------------------

class WriteStrategy(Enum):
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"


class WriteCache:
    """Write-through and write-behind cache strategies."""

    def __init__(self, store: TieredStore, backend: Callable | None = None,
                 strategy: WriteStrategy = WriteStrategy.WRITE_THROUGH):
        self.store = store
        self.backend = backend
        self.strategy = strategy
        self._pending_writes: list[tuple[str, Any]] = []
        self._lock = threading.Lock()
        self._flush_executor = ThreadPoolExecutor(max_workers=1)

    def write(self, key: str, value: Any) -> Any:
        self.store.set(key, value)

        if self.strategy == WriteStrategy.WRITE_THROUGH:
            if self.backend:
                self.backend(key, value)
        else:
            with self._lock:
                self._pending_writes.append((key, value))

        return value

    def flush(self):
        if self.strategy != WriteStrategy.WRITE_BEHIND or not self.backend:
            return
        with self._lock:
            pending = list(self._pending_writes)
            self._pending_writes.clear()

        for key, value in pending:
            try:
                self.backend(key, value)
            except Exception as exc:
                logger.warning("Write-behind flush failed for %s: %s", key, exc)

    @property
    def pending_count(self) -> int:
        return len(self._pending_writes)


# ---------------------------------------------------------------------------
# Idea 1 - Main Multi-Tier Cache orchestrator
# ---------------------------------------------------------------------------

class MultiTierCache:
    """
    Orchestrates L1 (memory), L2 (Redis-sim), L3 (CDN-sim) caching.
    """

    def __init__(
        self,
        l1_size: int = 500,
        l2_size: int = 5000,
        l3_size: int = 50000,
        default_ttl: float = 300,
    ):
        self.l1 = TieredStore("L1_memory", max_size=l1_size, default_ttl=default_ttl)
        self.l2 = TieredStore("L2_redis", max_size=l2_size, default_ttl=default_ttl)
        self.l3 = TieredStore("L3_cdn", max_size=l3_size, default_ttl=default_ttl)
        self.metrics = CacheMetrics()
        self.invalidator = CacheInvalidator()
        self.warmer = CacheWarmer()
        self.stampede = StampedePreventer()

    def get(self, key: str) -> Any | None:
        start = time.monotonic()

        # L1
        value = self.l1.get(key)
        if value is not None:
            self.metrics.record_hit()
            self.metrics.record_latency((time.monotonic() - start) * 1_000_000)
            return value

        # L2
        value = self.l2.get(key)
        if value is not None:
            self.l1.set(key, value)
            self.metrics.record_hit()
            self.metrics.record_latency((time.monotonic() - start) * 1_000_000)
            return value

        # L3
        value = self.l3.get(key)
        if value is not None:
            self.l2.set(key, value)
            self.l1.set(key, value)
            self.metrics.record_hit()
            self.metrics.record_latency((time.monotonic() - start) * 1_000_000)
            return value

        self.metrics.record_miss()
        self.metrics.record_latency((time.monotonic() - start) * 1_000_000)
        return None

    def set(self, key: str, value: Any, ttl: float | None = None):
        self.l1.set(key, value, ttl=ttl)
        self.l2.set(key, value, ttl=ttl)
        self.l3.set(key, value, ttl=ttl)
        self.metrics.record_set()

    def get_or_load(self, key: str, loader: Callable, ttl: float | None = None) -> Any:
        value = self.get(key)
        if value is not None:
            return value
        value = self.stampede.do_once(key, loader)
        self.set(key, value, ttl=ttl)
        return value

    def invalidate(self, key: str):
        self.l1.delete(key)
        self.l2.delete(key)
        self.l3.delete(key)
        self.invalidator.invalidate("manual", [key])

    def clear(self):
        self.l1.clear()
        self.l2.clear()
        self.l3.clear()

    def stats(self) -> dict[str, Any]:
        return {
            "l1": self.l1.stats(),
            "l2": self.l2.stats(),
            "l3": self.l3.stats(),
            "global": self.metrics.report(),
            "warmed_keys": self.warmer.warmed_count,
            "invalidation_log_count": self.invalidator.log_count,
        }


# ---------------------------------------------------------------------------
# Pre-configured singleton for quick use
# ---------------------------------------------------------------------------

default_cache = MultiTierCache()

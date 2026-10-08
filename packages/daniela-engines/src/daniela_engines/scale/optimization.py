"""
Performance Optimization (Ideas 41-50)
--------------------------------------
Query plan analyzer, N+1 detector, memory allocator, CPU cache-friendly structures,
lazy loading, object pool, string interning, binary protocols, batch processing,
startup time optimizer.
"""

from __future__ import annotations

import gc
import json
import logging
import threading
import time
import tracemalloc
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Idea 41 - Query plan analyzer
# ---------------------------------------------------------------------------

class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    JOIN = "JOIN"
    AGGREGATE = "AGGREGATE"


@dataclass
class QueryStep:
    operation: str
    table: str
    cost_estimate: float
    rows_estimate: int
    index_used: bool = False
    children: list[QueryStep] = field(default_factory=list)


@dataclass
class QueryPlan:
    query_type: QueryType
    steps: list[QueryStep]
    total_cost: float = 0.0
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class QueryPlanAnalyzer:
    """Analyze query execution plans and suggest optimizations."""

    def __init__(self):
        self._plans: list[QueryPlan] = []

    def analyze(self, plan: QueryPlan) -> QueryPlan:
        self._plans.append(plan)
        plan.warnings.clear()
        plan.suggestions.clear()
        plan.total_cost = sum(s.cost_estimate for s in plan.steps)

        for step in plan.steps:
            if not step.index_used and step.rows_estimate > 1000:
                plan.warnings.append(f"Full scan on '{step.table}' ({step.rows_estimate} rows)")
                plan.suggestions.append(f"Add index on '{step.table}'")
            if step.cost_estimate > 1000:
                plan.warnings.append(f"High cost step: {step.operation} on '{step.table}'")
            self._analyze_children(step, plan)

        return plan

    def _analyze_children(self, step: QueryStep, plan: QueryPlan):
        for child in step.children:
            if not child.index_used and child.rows_estimate > 5000:
                plan.suggestions.append(f"Nested loop: index '{child.table}'")
            self._analyze_children(child, plan)

    def get_stats(self) -> dict[str, Any]:
        if not self._plans:
            return {"analyzed": 0}
        costs = [p.total_cost for p in self._plans]
        return {
            "analyzed": len(self._plans),
            "avg_cost": round(sum(costs) / len(costs), 2),
            "max_cost": round(max(costs), 2),
            "total_warnings": sum(len(p.warnings) for p in self._plans),
            "total_suggestions": sum(len(p.suggestions) for p in self._plans),
        }


# ---------------------------------------------------------------------------
# Idea 42 - N+1 query detector
# ---------------------------------------------------------------------------

class NPlusOneDetector:
    """Detect N+1 query patterns in code."""

    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self._query_groups: dict[str, list[float]] = defaultdict(list)
        self._violations: list[dict[str, Any]] = []

    def record_query(self, operation: str, table: str, context: str = ""):
        key = f"{operation}:{table}:{context}"
        self._query_groups[key].append(time.time())

    def detect(self) -> list[dict[str, Any]]:
        violations = []
        for key, timestamps in self._query_groups.items():
            if len(timestamps) >= self.threshold:
                operation, table, _ = key.split(":", 2)
                violation = {
                    "operation": operation,
                    "table": table,
                    "count": len(timestamps),
                    "timespan_ms": round((timestamps[-1] - timestamps[0]) * 1000, 2),
                    "suggestion": f"Batch {operation} on '{table}' (detected {len(timestamps)} calls)",
                }
                violations.append(violation)
                self._violations.append(violation)
        return violations

    def stats(self) -> dict[str, Any]:
        return {
            "query_groups": len(self._query_groups),
            "total_queries": sum(len(v) for v in self._query_groups.values()),
            "violations": len(self._violations),
        }


# ---------------------------------------------------------------------------
# Idea 43 - Memory allocation optimizer
# ---------------------------------------------------------------------------

class MemoryAllocatorOptimizer:
    """Track and optimize memory allocation patterns."""

    def __init__(self):
        self._snapshots: list[tuple[str, int, int]] = []
        self._pool: dict[int, list[bytes]] = {}
        self._allocations = 0
        self._deallocations = 0
        self._lock = threading.Lock()

    def start_tracking(self, label: str = ""):
        tracemalloc.start()
        self._snapshots.append((label, 0, 0))

    def stop_tracking(self) -> dict[str, Any]:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if self._snapshots:
            label = self._snapshots[-1][0]
            self._snapshots[-1] = (label, current, peak)
        return {"current_bytes": current, "peak_bytes": peak}

    def allocate(self, size: int) -> bytes:
        with self._lock:
            self._allocations += 1
            if size in self._pool and self._pool[size]:
                return self._pool[size].pop()
        return b"\x00" * size

    def deallocate(self, data: bytes):
        size = len(data)
        with self._lock:
            self._deallocations += 1
            if size not in self._pool:
                self._pool[size] = []
            if len(self._pool[size]) < 100:
                self._pool[size].append(data)

    def force_gc(self):
        gc.collect()

    def stats(self) -> dict[str, Any]:
        with self._lock:
            pool_stats = {size: len(bufs) for size, bufs in self._pool.items()}
        return {
            "allocations": self._allocations,
            "deallocations": self._deallocations,
            "pool_sizes": pool_stats,
            "tracemalloc_snapshots": [
                {"label": s[0], "current": s[1], "peak": s[2]} for s in self._snapshots
            ],
        }


# ---------------------------------------------------------------------------
# Idea 44 - CPU cache-friendly data structures
# ---------------------------------------------------------------------------

class CacheFriendlyArray:
    """Dense array optimized for CPU cache locality."""

    def __init__(self, dtype_size: int = 8, initial_capacity: int = 64):
        self.dtype_size = dtype_size
        self._data = bytearray(initial_capacity * dtype_size)
        self._size = 0
        self._capacity = initial_capacity

    def append(self, value: int):
        if self._size >= self._capacity:
            self._grow()
        offset = self._size * self.dtype_size
        self._data[offset:offset + self.dtype_size] = value.to_bytes(self.dtype_size, "little")
        self._size += 1

    def get(self, index: int) -> int:
        if index < 0 or index >= self._size:
            raise IndexError(f"Index {index} out of range [0, {self._size})")
        offset = index * self.dtype_size
        return int.from_bytes(self._data[offset:offset + self.dtype_size], "little")

    def _grow(self):
        new_cap = self._capacity * 2
        new_data = bytearray(new_cap * self.dtype_size)
        new_data[:self._size * self.dtype_size] = self._data[:self._size * self.dtype_size]
        self._data = new_data
        self._capacity = new_cap

    def __len__(self) -> int:
        return self._size

    def to_list(self) -> list[int]:
        result = []
        for i in range(self._size):
            result.append(self.get(i))
        return result


class SOAStructure:
    """Structure of Arrays for cache-friendly iteration over one field."""

    def __init__(self):
        self._arrays: dict[str, list] = {}
        self._length = 0

    def add_field(self, name: str):
        self._arrays[name] = []

    def append(self, **kwargs):
        for name, value in kwargs.items():
            if name not in self._arrays:
                self._arrays[name] = []
            self._arrays[name].append(value)
        self._length += 1

    def get_field(self, name: str) -> list:
        return self._arrays.get(name, [])

    def __len__(self) -> int:
        return self._length


# ---------------------------------------------------------------------------
# Idea 45 - Lazy loading manager
# ---------------------------------------------------------------------------

class LazyLoader:
    """Lazy load expensive computations with thread-safe initialization."""

    def __init__(self):
        self._factories: dict[str, Callable] = {}
        self._cache: dict[str, Any] = {}
        self._loading: dict[str, bool] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    def register(self, key: str, factory: Callable):
        with self._global_lock:
            self._factories[key] = factory
            self._locks[key] = threading.Lock()

    def get(self, key: str) -> Any:
        if key in self._cache:
            return self._cache[key]

        with self._global_lock:
            if key not in self._locks:
                raise KeyError(f"No factory registered for '{key}'")
            lock = self._locks[key]

        with lock:
            if key in self._cache:
                return self._cache[key]
            value = self._factories[key]()
            self._cache[key] = value
            return value

    def is_loaded(self, key: str) -> bool:
        return key in self._cache

    def invalidate(self, key: str):
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()

    def stats(self) -> dict[str, Any]:
        return {
            "registered": list(self._factories.keys()),
            "loaded": list(self._cache.keys()),
            "pending": [k for k in self._factories if k not in self._cache],
        }


# ---------------------------------------------------------------------------
# Idea 46 - Object pool (reuse instances)
# ---------------------------------------------------------------------------

class ObjectPool:
    """Reuse expensive-to-create objects."""

    def __init__(self, factory: Callable[[], T], max_size: int = 50):
        self.factory = factory
        self.max_size = max_size
        self._pool: list[T] = []
        self._lock = threading.Lock()
        self._total_created = 0
        self._total_reused = 0

    def acquire(self) -> T:
        with self._lock:
            if self._pool:
                obj = self._pool.pop()
                self._total_reused += 1
                return obj
        obj = self.factory()
        self._total_created += 1
        return obj

    def release(self, obj: T):
        with self._lock:
            if len(self._pool) < self.max_size:
                self._pool.append(obj)

    @property
    def idle_count(self) -> int:
        return len(self._pool)

    def stats(self) -> dict[str, Any]:
        return {
            "idle": self.idle_count,
            "max_size": self.max_size,
            "total_created": self._total_created,
            "total_reused": self._total_reused,
            "reuse_rate": round(self._total_reused / max(1, self._total_created + self._total_reused), 4),
        }


# ---------------------------------------------------------------------------
# Idea 47 - String interning
# ---------------------------------------------------------------------------

class StringInterner:
    """Intern strings to reduce memory for repeated values."""

    def __init__(self):
        self._pool: dict[str, str] = {}
        self._ref_counts: dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def intern(self, s: str) -> str:
        with self._lock:
            if s not in self._pool:
                self._pool[s] = s
            self._ref_counts[s] += 1
            return self._pool[s]

    def release(self, s: str):
        with self._lock:
            if s in self._ref_counts:
                self._ref_counts[s] -= 1
                if self._ref_counts[s] <= 0:
                    del self._pool[s]
                    del self._ref_counts[s]

    @property
    def unique_count(self) -> int:
        return len(self._pool)

    @property
    def total_references(self) -> int:
        return sum(self._ref_counts.values())

    def stats(self) -> dict[str, Any]:
        return {
            "unique_strings": self.unique_count,
            "total_references": self.total_references,
            "top_interned": sorted(
                self._ref_counts.items(), key=lambda x: -x[1]
            )[:10],
        }


# ---------------------------------------------------------------------------
# Idea 48 - Binary protocol optimization
# ---------------------------------------------------------------------------

class BinaryProtocolCodec:
    """Compact binary encoding/decoding for network protocols."""

    @staticmethod
    def encode_int(value: int) -> bytes:
        if value < 0:
            value = (value << 1) ^ (-1 if value < 0 else 0)
        result = bytearray()
        while value > 0x7F:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value & 0x7F)
        return bytes(result)

    @staticmethod
    def decode_int(data: bytes, offset: int = 0) -> tuple[int, int]:
        result = 0
        shift = 0
        pos = offset
        while pos < len(data):
            byte = data[pos]
            result |= (byte & 0x7F) << shift
            pos += 1
            if not (byte & 0x80):
                break
            shift += 7
        return result, pos

    @staticmethod
    def encode_string(s: str) -> bytes:
        encoded = s.encode("utf-8")
        return BinaryProtocolCodec.encode_int(len(encoded)) + encoded

    @staticmethod
    def decode_string(data: bytes, offset: int = 0) -> tuple[str, int]:
        length, pos = BinaryProtocolCodec.decode_int(data, offset)
        s = data[pos:pos + length].decode("utf-8")
        return s, pos + length

    @staticmethod
    def encode_dict(d: dict[str, Any]) -> bytes:
        parts = [BinaryProtocolCodec.encode_int(len(d))]
        for k, v in d.items():
            parts.append(BinaryProtocolCodec.encode_string(k))
            parts.append(BinaryProtocolCodec.encode_string(json.dumps(v)))
        return b"".join(parts)

    @staticmethod
    def decode_dict(data: bytes, offset: int = 0) -> tuple[dict[str, Any], int]:
        count, pos = BinaryProtocolCodec.decode_int(data, offset)
        result = {}
        for _ in range(count):
            key, pos = BinaryProtocolCodec.decode_string(data, pos)
            val_str, pos = BinaryProtocolCodec.decode_string(data, pos)
            result[key] = json.loads(val_str)
        return result, pos


# ---------------------------------------------------------------------------
# Idea 49 - Batch processing optimizer
# ---------------------------------------------------------------------------

class BatchProcessor:
    """Batch small operations for throughput optimization."""

    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer: list[Any] = []
        self._lock = threading.Lock()
        self._last_flush = time.time()
        self._total_processed = 0
        self._total_batches = 0
        self._process_fn: Callable | None = None

    def set_processor(self, fn: Callable[[list[Any]], Any]):
        self._process_fn = fn

    def add(self, item: Any):
        with self._lock:
            self._buffer.append(item)
            if len(self._buffer) >= self.batch_size:
                self._flush_locked()

    def flush(self) -> Any | None:
        with self._lock:
            return self._flush_locked()

    def _flush_locked(self) -> Any | None:
        if not self._buffer or not self._process_fn:
            return None
        batch = self._buffer[:]
        self._buffer.clear()
        self._last_flush = time.time()
        self._total_batches += 1
        self._total_processed += len(batch)
        return self._process_fn(batch)

    def auto_flush_check(self) -> Any | None:
        with self._lock:
            if time.time() - self._last_flush >= self.flush_interval and self._buffer:
                return self._flush_locked()
        return None

    @property
    def pending_count(self) -> int:
        return len(self._buffer)

    def stats(self) -> dict[str, Any]:
        return {
            "pending": self.pending_count,
            "total_processed": self._total_processed,
            "total_batches": self._total_batches,
            "avg_batch_size": round(self._total_processed / max(1, self._total_batches), 1),
            "batch_size_limit": self.batch_size,
        }


# ---------------------------------------------------------------------------
# Idea 50 - Startup time optimizer
# ---------------------------------------------------------------------------

class StartupOptimizer:
    """Defer and parallelize startup initialization."""

    def __init__(self):
        self._deferred: dict[str, Callable] = {}
        self._loaded: set[str] = set()
        self._load_times: dict[str, float] = {}
        self._lock = threading.Lock()

    def defer(self, name: str, init_fn: Callable):
        with self._lock:
            self._deferred[name] = init_fn

    def load(self, name: str) -> Any:
        if name in self._loaded:
            return None

        if name not in self._deferred:
            raise KeyError(f"No deferred init for '{name}'")

        start = time.monotonic()
        result = self._deferred[name]()
        elapsed = (time.monotonic() - start) * 1000

        with self._lock:
            self._loaded.add(name)
            self._load_times[name] = elapsed
        return result

    def load_all(self) -> dict[str, float]:
        times = {}
        for name in list(self._deferred.keys()):
            if name not in self._loaded:
                self.load(name)
                times[name] = self._load_times.get(name, 0)
        return times

    def load_parallel(self, names: list[str] | None = None) -> dict[str, float]:
        targets = names or [n for n in self._deferred if n not in self._loaded]
        executor = ThreadPoolExecutor(max_workers=min(len(targets), 8))
        futures = {}

        for name in targets:
            if name in self._loaded:
                continue
            futures[name] = executor.submit(self.load, name)

        times = {}
        for name, fut in futures.items():
            try:
                fut.result(timeout=30)
                times[name] = self._load_times.get(name, 0)
            except Exception as exc:
                logger.warning("Parallel load failed for %s: %s", name, exc)

        executor.shutdown(wait=False)
        return times

    def stats(self) -> dict[str, Any]:
        return {
            "deferred": list(self._deferred.keys()),
            "loaded": list(self._loaded),
            "pending": [n for n in self._deferred if n not in self._loaded],
            "load_times_ms": {k: round(v, 3) for k, v in self._load_times.items()},
            "total_time_ms": round(sum(self._load_times.values()), 3),
        }


# ---------------------------------------------------------------------------
# Unified Optimization Manager
# ---------------------------------------------------------------------------

class OptimizationManager:
    """Unified interface to all optimization tools."""

    def __init__(self):
        self.query_analyzer = QueryPlanAnalyzer()
        self.n_plus_one_detector = NPlusOneDetector()
        self.memory_optimizer = MemoryAllocatorOptimizer()
        self.lazy_loader = LazyLoader()
        self.string_interner = StringInterner()
        self.batch_processor = BatchProcessor()
        self.startup_optimizer = StartupOptimizer()
        self._object_pools: dict[str, ObjectPool] = {}

    def get_object_pool(self, name: str, factory: Callable, max_size: int = 50) -> ObjectPool:
        if name not in self._object_pools:
            self._object_pools[name] = ObjectPool(factory=factory, max_size=max_size)
        return self._object_pools[name]

    def stats(self) -> dict[str, Any]:
        return {
            "query_analyzer": self.query_analyzer.get_stats(),
            "n_plus_one": self.n_plus_one_detector.stats(),
            "memory": self.memory_optimizer.stats(),
            "lazy_loader": self.lazy_loader.stats(),
            "string_interner": self.string_interner.stats(),
            "batch_processor": self.batch_processor.stats(),
            "startup": self.startup_optimizer.stats(),
            "object_pools": {k: v.stats() for k, v in self._object_pools.items()},
        }

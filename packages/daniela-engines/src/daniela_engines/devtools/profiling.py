"""Profiling tools (41-50)."""

import cProfile
import gc
import io
import os
import pstats
import re
import sys
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any


@dataclass
class FunctionCall:
    name: str
    call_count: int
    total_time_ms: float
    own_time_ms: float
    avg_time_ms: float
    callers: list


@dataclass
class QueryProfile:
    query: str
    duration_ms: float
    timestamp: float
    call_stack: list


@dataclass
class CacheMetric:
    key: str
    hits: int
    misses: int
    hit_rate: float
    avg_hit_time_ms: float
    avg_miss_time_ms: float


@dataclass
class LatencySample:
    target: str
    latency_ms: float
    timestamp: float
    success: bool
    error: str | None = None


@dataclass
class AllocationInfo:
    obj_type: str
    count: int
    total_size: int
    avg_size: int


@dataclass
class GCEvent:
    generation: int
    collected: int
    duration_ms: float
    timestamp: float
    freed_bytes: int


@dataclass
class AsyncEvent:
    coroutine: str
    event_type: str
    duration_ms: float
    timestamp: float
    loop_time_ms: float


@dataclass
class ConcurrencyMetric:
    thread_name: str
    cpu_time_ms: float
    wall_time_ms: float
    idle_time_ms: float
    task_count: int


@dataclass
class StartupPhase:
    name: str
    duration_ms: float
    cumulative_ms: float
    description: str


@dataclass
class BundleEntry:
    name: str
    size_bytes: int
    type: str
    gzip_bytes: int | None = None


class FunctionCallTracer:
    """41. Function call tracer."""

    def __init__(self):
        self._calls: list[FunctionCall] = []
        self._active: bool = False
        self._profiler: cProfile.Profile | None = None

    def start(self) -> None:
        self._active = True
        self._profiler = cProfile.Profile()
        self._profiler.enable()

    def stop(self) -> list[FunctionCall]:
        self._active = False
        if self._profiler:
            self._profiler.disable()
        return self._process_results()

    def _process_results(self) -> list[FunctionCall]:
        if not self._profiler:
            return []
        stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        stats.sort_stats("cumulative")

        calls = []
        for func_key, (_cc, nc, tt, ct, callers) in stats.stats.items():
            filename, lineno, func_name = func_key
            calls.append(
                FunctionCall(
                    name=f"{func_name} ({filename}:{lineno})",
                    call_count=nc,
                    total_time_ms=round(ct * 1000, 3),
                    own_time_ms=round(tt * 1000, 3),
                    avg_time_ms=round((tt / nc * 1000) if nc else 0, 3),
                    callers=[
                        f"{ck[2]} ({ck[0]}:{ck[1]})" for ck in callers.keys()
                    ],
                )
            )
        calls.sort(key=lambda c: c.total_time_ms, reverse=True)
        self._calls = calls
        return calls

    def trace_function(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            self._active = True
            if not self._profiler:
                self._profiler = cProfile.Profile()
            self._profiler.enable()
            try:
                return func(*args, **kwargs)
            finally:
                self._profiler.disable()
                self._active = False

        return wrapper

    def get_top_calls(self, n: int = 10) -> list[dict]:
        return [
            {
                "name": c.name,
                "total_ms": c.total_time_ms,
                "own_ms": c.own_time_ms,
                "calls": c.call_count,
            }
            for c in self._calls[:n]
        ]

    def get_call_stats(self) -> dict:
        if not self._calls:
            return {"total_calls": 0, "total_time_ms": 0}
        return {
            "total_calls": sum(c.call_count for c in self._calls),
            "total_time_ms": round(sum(c.total_time_ms for c in self._calls), 3),
            "unique_functions": len(self._calls),
            "avg_time_ms": round(
                sum(c.avg_time_ms for c in self._calls) / len(self._calls), 3
            ),
        }


class DatabaseQueryProfiler:
    """42. Database query profiler."""

    def __init__(self):
        self._queries: list[QueryProfile] = []
        self._slow_threshold_ms: float = 100.0

    def profile_query(self, query: str, duration_ms: float, call_stack: list | None = None) -> QueryProfile:
        qp = QueryProfile(
            query=query.strip(),
            duration_ms=duration_ms,
            timestamp=time.time(),
            call_stack=call_stack or [],
        )
        self._queries.append(qp)
        return qp

    def get_slow_queries(self, threshold_ms: float | None = None) -> list[QueryProfile]:
        threshold = threshold_ms or self._slow_threshold_ms
        return [q for q in self._queries if q.duration_ms > threshold]

    def get_summary(self) -> dict:
        if not self._queries:
            return {"total_queries": 0, "avg_duration_ms": 0, "slow_count": 0}
        durations = [q.duration_ms for q in self._queries]
        return {
            "total_queries": len(self._queries),
            "avg_duration_ms": round(sum(durations) / len(durations), 2),
            "max_duration_ms": round(max(durations), 2),
            "min_duration_ms": round(min(durations), 2),
            "slow_count": len(self.get_slow_queries()),
            "total_time_ms": round(sum(durations), 2),
        }

    def get_by_pattern(self) -> dict:
        patterns = defaultdict(list)
        for q in self._queries:
            normalized = re.sub(r"\d+", "?", q.query)[:100]
            patterns[normalized].append(q.duration_ms)
        result = {}
        for pattern, durations in patterns.items():
            result[pattern] = {
                "count": len(durations),
                "avg_ms": round(sum(durations) / len(durations), 2),
                "max_ms": round(max(durations), 2),
            }
        return result

    def get_timeline(self) -> list[dict]:
        return [
            {"timestamp": q.timestamp, "query": q.query[:80], "duration_ms": q.duration_ms}
            for q in self._queries
        ]


class CacheHitMissAnalyzer:
    """43. Cache hit/miss analyzer."""

    def __init__(self):
        self._metrics: dict[str, dict] = defaultdict(
            lambda: {"hits": 0, "misses": 0, "hit_times": [], "miss_times": []}
        )

    def record_hit(self, key: str, duration_ms: float = 0) -> None:
        self._metrics[key]["hits"] += 1
        self._metrics[key]["hit_times"].append(duration_ms)

    def record_miss(self, key: str, duration_ms: float = 0) -> None:
        self._metrics[key]["misses"] += 1
        self._metrics[key]["miss_times"].append(duration_ms)

    def get_metrics(self) -> list[CacheMetric]:
        results = []
        for key, m in self._metrics.items():
            total = m["hits"] + m["misses"]
            hit_rate = m["hits"] / total if total > 0 else 0
            avg_hit = sum(m["hit_times"]) / len(m["hit_times"]) if m["hit_times"] else 0
            avg_miss = sum(m["miss_times"]) / len(m["miss_times"]) if m["miss_times"] else 0
            results.append(
                CacheMetric(
                    key=key,
                    hits=m["hits"],
                    misses=m["misses"],
                    hit_rate=round(hit_rate, 4),
                    avg_hit_time_ms=round(avg_hit, 3),
                    avg_miss_time_ms=round(avg_miss, 3),
                )
            )
        return results

    def get_overall_stats(self) -> dict:
        total_hits = sum(m["hits"] for m in self._metrics.values())
        total_misses = sum(m["misses"] for m in self._metrics.values())
        total = total_hits + total_misses
        return {
            "total_requests": total,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "overall_hit_rate": round(total_hits / total, 4) if total > 0 else 0,
            "unique_keys": len(self._metrics),
        }

    def get_worst_performing(self, n: int = 5) -> list[dict]:
        metrics = self.get_metrics()
        metrics.sort(key=lambda m: m.hit_rate)
        return [
            {"key": m.key, "hit_rate": m.hit_rate, "total": m.hits + m.misses}
            for m in metrics[:n]
        ]


class NetworkLatencyProfiler:
    """44. Network latency profiler."""

    def __init__(self):
        self._samples: list[LatencySample] = []

    def record(self, target: str, latency_ms: float, success: bool = True, error: str | None = None) -> LatencySample:
        sample = LatencySample(
            target=target,
            latency_ms=latency_ms,
            timestamp=time.time(),
            success=success,
            error=error,
        )
        self._samples.append(sample)
        return sample

    def get_stats(self, target: str | None = None) -> dict:
        samples = [s for s in self._samples if target is None or s.target == target]
        if not samples:
            return {"count": 0}
        latencies = [s.latency_ms for s in samples]
        success_count = sum(1 for s in samples if s.success)
        return {
            "count": len(samples),
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "p50_ms": round(sorted(latencies)[len(latencies) // 2], 2),
            "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if len(latencies) >= 20 else round(max(latencies), 2),
            "p99_ms": round(sorted(latencies)[int(len(latencies) * 0.99)], 2) if len(latencies) >= 100 else round(max(latencies), 2),
            "success_rate": round(success_count / len(samples), 4),
            "error_count": len(samples) - success_count,
        }

    def get_by_target(self) -> dict:
        by_target = defaultdict(list)
        for s in self._samples:
            by_target[s.target].append(s.latency_ms)
        return {
            target: {
                "count": len(latencies),
                "avg_ms": round(sum(latencies) / len(latencies), 2),
                "max_ms": round(max(latencies), 2),
            }
            for target, latencies in by_target.items()
        }

    def get_percentiles(self, target: str | None = None) -> dict:
        samples = [s for s in self._samples if target is None or s.target == target]
        if not samples:
            return {}
        latencies = sorted(s.latency_ms for s in samples)
        n = len(latencies)
        percentiles = {}
        for p in [50, 75, 90, 95, 99]:
            idx = int(n * p / 100)
            percentiles[f"p{p}"] = round(latencies[min(idx, n - 1)], 2)
        return percentiles


class MemoryAllocationTracker:
    """45. Memory allocation tracker."""

    def __init__(self):
        self._snapshots: list[dict] = []
        self._allocations: dict[str, list[int]] = defaultdict(list)

    def take_snapshot(self) -> dict:
        gc.collect()
        objects = gc.get_objects()
        type_counts = defaultdict(int)
        type_sizes = defaultdict(int)
        for obj in objects:
            type_name = type(obj).__name__
            type_counts[type_name] += 1
            try:
                type_sizes[type_name] += sys.getsizeof(obj)
            except (TypeError, RecursionError):
                pass

        snapshot = {
            "timestamp": time.time(),
            "total_objects": len(objects),
            "total_size_mb": round(sum(type_sizes.values()) / (1024 * 1024), 2),
            "top_types": dict(
                sorted(type_counts.items(), key=lambda x: -x[1])[:20]
            ),
            "top_sizes": dict(
                sorted(type_sizes.items(), key=lambda x: -x[1])[:20]
            ),
        }
        self._snapshots.append(snapshot)
        return snapshot

    def track_type(self, type_name: str) -> None:
        gc.collect()
        count = sum(
            1 for obj in gc.get_objects() if type(obj).__name__ == type_name
        )
        self._allocations[type_name].append(count)

    def get_growth(self, type_name: str) -> list[dict]:
        counts = self._allocations.get(type_name, [])
        if len(counts) < 2:
            return []
        return [
            {"index": i, "count": counts[i], "delta": counts[i] - counts[i - 1] if i > 0 else 0}
            for i in range(len(counts))
        ]

    def get_snapshots(self) -> list[dict]:
        return self._snapshots

    def get_diff(self) -> dict | None:
        if len(self._snapshots) < 2:
            return None
        first = self._snapshots[0]
        last = self._snapshots[-1]
        return {
            "object_delta": last["total_objects"] - first["total_objects"],
            "size_delta_mb": round(last["total_size_mb"] - first["total_size_mb"], 2),
            "snapshots": len(self._snapshots),
        }


class GarbageCollectionMonitor:
    """46. Garbage collection monitor."""

    def __init__(self):
        self._events: list[GCEvent] = []
        self._original_callback = None

    def start(self) -> None:
        gc.callbacks.append(self._on_gc)
        gc.set_debug(0)

    def stop(self) -> None:
        try:
            gc.callbacks.remove(self._on_gc)
        except ValueError:
            pass

    def _on_gc(self, info: Any, action: str, obj_type: Any) -> None:
        if action == "stop":
            return

    def manual_collect(self, generation: int = 2) -> GCEvent:
        start = time.time()
        collected = gc.collect(generation)
        duration = (time.time() - start) * 1000
        event = GCEvent(
            generation=generation,
            collected=collected,
            duration_ms=round(duration, 3),
            timestamp=time.time(),
            freed_bytes=0,
        )
        self._events.append(event)
        return event

    def get_stats(self) -> dict:
        gen_counts = defaultdict(int)
        total_collected = 0
        for e in self._events:
            gen_counts[e.generation] += 1
            total_collected += e.collected
        return {
            "total_collections": len(self._events),
            "total_collected": total_collected,
            "by_generation": dict(gen_counts),
            "avg_duration_ms": round(
                sum(e.duration_ms for e in self._events) / len(self._events), 3
            )
            if self._events
            else 0,
        }

    def get_events(self) -> list[dict]:
        return [
            {
                "generation": e.generation,
                "collected": e.collected,
                "duration_ms": e.duration_ms,
                "timestamp": e.timestamp,
            }
            for e in self._events
        ]

    def get_stats_by_generation(self) -> dict:
        by_gen = defaultdict(lambda: {"count": 0, "collected": 0, "total_ms": 0})
        for e in self._events:
            by_gen[e.generation]["count"] += 1
            by_gen[e.generation]["collected"] += e.collected
            by_gen[e.generation]["total_ms"] += e.duration_ms
        return {str(k): v for k, v in by_gen.items()}


class EventLoopAnalyzer:
    """47. Event loop analyzer (async)."""

    def __init__(self):
        self._events: list[AsyncEvent] = []
        self._loop_stats: dict = defaultdict(lambda: {"count": 0, "total_ms": 0})

    def record_event(self, coroutine: str, event_type: str, duration_ms: float) -> AsyncEvent:
        event = AsyncEvent(
            coroutine=coroutine,
            event_type=event_type,
            duration_ms=duration_ms,
            timestamp=time.time(),
            loop_time_ms=0,
        )
        self._events.append(event)
        self._loop_stats[coroutine]["count"] += 1
        self._loop_stats[coroutine]["total_ms"] += duration_ms
        return event

    def get_stats(self) -> dict:
        if not self._events:
            return {"total_events": 0}
        durations = [e.duration_ms for e in self._events]
        return {
            "total_events": len(self._events),
            "avg_duration_ms": round(sum(durations) / len(durations), 3),
            "max_duration_ms": round(max(durations), 3),
            "unique_coroutines": len(self._loop_stats),
        }

    def get_slow_coroutines(self, n: int = 10) -> list[dict]:
        stats = []
        for name, data in self._loop_stats.items():
            stats.append(
                {
                    "coroutine": name,
                    "count": data["count"],
                    "total_ms": round(data["total_ms"], 3),
                    "avg_ms": round(data["total_ms"] / data["count"], 3),
                }
            )
        stats.sort(key=lambda s: s["total_ms"], reverse=True)
        return stats[:n]

    def get_events(self) -> list[dict]:
        return [
            {
                "coroutine": e.coroutine,
                "type": e.event_type,
                "duration_ms": e.duration_ms,
                "timestamp": e.timestamp,
            }
            for e in self._events
        ]


class ConcurrencyProfiler:
    """48. Concurrency profiler."""

    def __init__(self):
        self._metrics: list[ConcurrencyMetric] = []

    def record_thread(
        self,
        thread_name: str,
        cpu_time_ms: float,
        wall_time_ms: float,
        task_count: int = 1,
    ) -> ConcurrencyMetric:
        idle = max(0, wall_time_ms - cpu_time_ms)
        metric = ConcurrencyMetric(
            thread_name=thread_name,
            cpu_time_ms=cpu_time_ms,
            wall_time_ms=wall_time_ms,
            idle_time_ms=round(idle, 3),
            task_count=task_count,
        )
        self._metrics.append(metric)
        return metric

    def get_summary(self) -> dict:
        if not self._metrics:
            return {"threads": 0}
        total_cpu = sum(m.cpu_time_ms for m in self._metrics)
        total_wall = sum(m.wall_time_ms for m in self._metrics)
        return {
            "threads": len(self._metrics),
            "total_cpu_ms": round(total_cpu, 3),
            "total_wall_ms": round(total_wall, 3),
            "cpu_utilization": round(total_cpu / total_wall, 4) if total_wall > 0 else 0,
            "total_tasks": sum(m.task_count for m in self._metrics),
        }

    def get_thread_details(self) -> list[dict]:
        return [
            {
                "name": m.thread_name,
                "cpu_ms": m.cpu_time_ms,
                "wall_ms": m.wall_time_ms,
                "idle_ms": m.idle_time_ms,
                "utilization": round(m.cpu_time_ms / m.wall_time_ms, 4) if m.wall_time_ms > 0 else 0,
                "tasks": m.task_count,
            }
            for m in self._metrics
        ]

    def find_bottlenecks(self) -> list[dict]:
        return [
            {"name": m.thread_name, "utilization": round(m.cpu_time_ms / m.wall_time_ms, 4) if m.wall_time_ms > 0 else 0}
            for m in self._metrics
            if m.wall_time_ms > 0 and m.cpu_time_ms / m.wall_time_ms < 0.3
        ]


class StartupTimeAnalyzer:
    """49. Startup time analyzer."""

    def __init__(self):
        self._phases: list[StartupPhase] = []
        self._start_time: float = 0

    def start(self) -> None:
        self._start_time = time.perf_counter()
        self._phases.clear()

    def mark_phase(self, name: str, description: str = "") -> StartupPhase:
        now = time.perf_counter()
        duration = (now - (self._start_time if not self._phases else self._phases[-1].cumulative_ms / 1000 + self._start_time)) * 1000
        cumulative = (now - self._start_time) * 1000
        phase = StartupPhase(
            name=name,
            duration_ms=round(duration, 3),
            cumulative_ms=round(cumulative, 3),
            description=description,
        )
        self._phases.append(phase)
        return phase

    def get_total_time(self) -> float:
        if not self._phases:
            return 0
        return self._phases[-1].cumulative_ms

    def get_phases(self) -> list[dict]:
        total = self.get_total_time()
        return [
            {
                "name": p.name,
                "duration_ms": p.duration_ms,
                "cumulative_ms": p.cumulative_ms,
                "percentage": round(p.duration_ms / total * 100, 1) if total > 0 else 0,
                "description": p.description,
            }
            for p in self._phases
        ]

    def get_slowest_phases(self, n: int = 5) -> list[dict]:
        sorted_phases = sorted(self._phases, key=lambda p: p.duration_ms, reverse=True)
        return [
            {"name": p.name, "duration_ms": p.duration_ms}
            for p in sorted_phases[:n]
        ]

    def get_timeline(self) -> str:
        if not self._phases:
            return "No phases recorded."
        total = self.get_total_time()
        lines = ["Startup Timeline:", "=" * 50]
        for p in self._phases:
            bar_len = int(p.duration_ms / total * 40) if total > 0 else 0
            bar = "#" * bar_len
            lines.append(f"  {p.name:30s} {p.duration_ms:8.1f}ms |{bar}")
        lines.append(f"  {'TOTAL':30s} {total:8.1f}ms")
        return "\n".join(lines)


class BundleSizeAnalyzer:
    """50. Bundle size analyzer."""

    def __init__(self):
        self._entries: list[BundleEntry] = []

    def analyze_directory(self, directory: str, extensions: list[str] | None = None) -> list[BundleEntry]:
        exts = extensions or [".js", ".css", ".py", ".json", ".html", ".png", ".jpg", ".svg"]
        self._entries.clear()
        for root, _, files in os.walk(directory):
            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                if ext in exts:
                    fp = os.path.join(root, fn)
                    size = os.path.getsize(fp)
                    rel_path = os.path.relpath(fp, directory)
                    self._entries.append(
                        BundleEntry(
                            name=rel_path,
                            size_bytes=size,
                            type=ext.lstrip(".") or "unknown",
                        )
                    )
        return self._entries

    def analyze_file(self, filepath: str) -> BundleEntry:
        size = os.path.getsize(filepath)
        ext = os.path.splitext(filepath)[1].lower()
        entry = BundleEntry(
            name=os.path.basename(filepath),
            size_bytes=size,
            type=ext.lstrip(".") or "unknown",
        )
        self._entries.append(entry)
        return entry

    def get_summary(self) -> dict:
        if not self._entries:
            return {"total_files": 0, "total_size_bytes": 0}
        by_type = defaultdict(lambda: {"count": 0, "size": 0})
        for e in self._entries:
            by_type[e.type]["count"] += 1
            by_type[e.type]["size"] += e.size_bytes
        return {
            "total_files": len(self._entries),
            "total_size_bytes": sum(e.size_bytes for e in self._entries),
            "total_size_mb": round(sum(e.size_bytes for e in self._entries) / (1024 * 1024), 2),
            "by_type": {
                k: {"count": v["count"], "size_mb": round(v["size"] / (1024 * 1024), 2)}
                for k, v in sorted(by_type.items(), key=lambda x: -x[1]["size"])
            },
        }

    def get_largest_files(self, n: int = 10) -> list[dict]:
        sorted_entries = sorted(self._entries, key=lambda e: e.size_bytes, reverse=True)
        return [
            {
                "name": e.name,
                "size_mb": round(e.size_bytes / (1024 * 1024), 2),
                "type": e.type,
            }
            for e in sorted_entries[:n]
        ]

    def get_type_breakdown(self) -> dict:
        by_type = defaultdict(lambda: {"count": 0, "total_bytes": 0})
        for e in self._entries:
            by_type[e.type]["count"] += 1
            by_type[e.type]["total_bytes"] += e.size_bytes
        return dict(by_type)

    def suggest_compression(self) -> list[dict]:
        suggestions = []
        for e in self._entries:
            if e.size_bytes > 100 * 1024:
                suggestions.append(
                    {
                        "file": e.name,
                        "size_kb": round(e.size_bytes / 1024, 1),
                        "suggestion": f"Consider compressing {e.name} ({e.type})",
                    }
                )
        return suggestions

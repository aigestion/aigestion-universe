"""Debugging tools (1-10)."""

import gc
import hashlib
import inspect
import json
import time
import traceback
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any


@dataclass
class VariableSnapshot:
    name: str
    value: Any
    type_name: str
    timestamp: float
    change_count: int = 0


@dataclass
class RequestLog:
    method: str
    url: str
    headers: dict
    body: Any
    response_status: int
    response_body: Any
    duration_ms: float
    timestamp: float


@dataclass
class StackFrame:
    filename: str
    lineno: int
    name: str
    code_context: str | None = None
    local_vars: dict = field(default_factory=dict)


@dataclass
class MemorySample:
    timestamp: float
    rss_bytes: int
    heap_bytes: int
    obj_count: int
    obj_types: dict = field(default_factory=dict)


@dataclass
class CPUProfileResult:
    total_time_ms: float
    function_calls: list
    hotspots: list
    call_counts: dict = field(default_factory=dict)


@dataclass
class IOProfileSample:
    timestamp: float
    disk_read_bytes: int
    disk_write_bytes: int
    net_sent_bytes: int
    net_recv_bytes: int
    open_files: int


@dataclass
class DeadlockInfo:
    threads: list
    waiting_on: dict
    detected_at: float
    severity: str = "critical"


@dataclass
class LeakCandidate:
    resource_type: str
    description: str
    age_seconds: float
    stack_trace: str
    severity: str


@dataclass
class Hotspot:
    function: str
    file: str
    line: int
    cumulative_time_ms: float
    own_time_ms: float
    call_count: int


@dataclass
class ReplayEvent:
    timestamp: float
    event_type: str
    data: dict
    session_id: str


class LiveVariableInspector:
    """1. Live variable inspector - tracks variable changes in real time."""

    def __init__(self):
        self._snapshots: dict[str, list[VariableSnapshot]] = defaultdict(list)
        self._watched: dict[str, Any] = {}
        self._tracking = False

    def watch(self, name: str, value: Any) -> None:
        self._watched[name] = value
        snap = VariableSnapshot(
            name=name,
            value=repr(value),
            type_name=type(value).__name__,
            timestamp=time.time(),
        )
        self._snapshots[name].append(snap)

    def unwatch(self, name: str) -> None:
        self._watched.pop(name, None)
        self._snapshots.pop(name, None)

    def update(self, name: str, new_value: Any) -> dict:
        old = self._watched.get(name)
        changed = old != new_value
        self._watched[name] = new_value
        snap = VariableSnapshot(
            name=name,
            value=repr(new_value),
            type_name=type(new_value).__name__,
            timestamp=time.time(),
            change_count=len(self._snapshots[name]) if changed else 0,
        )
        if changed:
            self._snapshots[name].append(snap)
        return {"changed": changed, "old": repr(old), "new": repr(new_value)}

    def get_history(self, name: str) -> list[dict]:
        return [
            {
                "value": s.value,
                "type": s.type_name,
                "timestamp": s.timestamp,
                "change_count": s.change_count,
            }
            for s in self._snapshots.get(name, [])
        ]

    def snapshot_all(self) -> dict[str, dict]:
        return {
            name: {"value": repr(val), "type": type(val).__name__}
            for name, val in self._watched.items()
        }

    def get_diff(self, name: str) -> list[dict]:
        snaps = self._snapshots.get(name, [])
        diffs = []
        for i in range(1, len(snaps)):
            diffs.append(
                {
                    "from": snaps[i - 1].value,
                    "to": snaps[i].value,
                    "at": snaps[i].timestamp,
                }
            )
        return diffs


class RequestResponseLogger:
    """2. Request/response logger for HTTP debugging."""

    def __init__(self, max_logs: int = 1000):
        self._logs: list[RequestLog] = []
        self._max_logs = max_logs
        self._filters: list[Callable] = []

    def add_filter(self, predicate: Callable[[RequestLog], bool]) -> None:
        self._filters.append(predicate)

    def log(
        self,
        method: str,
        url: str,
        headers: dict,
        body: Any,
        response_status: int,
        response_body: Any,
        duration_ms: float,
    ) -> RequestLog:
        entry = RequestLog(
            method=method,
            url=url,
            headers=headers,
            body=body,
            response_status=response_status,
            response_body=response_body,
            duration_ms=duration_ms,
            timestamp=time.time(),
        )
        if all(f(entry) for f in self._filters):
            self._logs.append(entry)
            if len(self._logs) > self._max_logs:
                self._logs.pop(0)
        return entry

    def get_logs(
        self,
        method: str | None = None,
        status_min: int | None = None,
        status_max: int | None = None,
        url_pattern: str | None = None,
    ) -> list[dict]:
        results = []
        for log in self._logs:
            if method and log.method != method:
                continue
            if status_min and log.response_status < status_min:
                continue
            if status_max and log.response_status > status_max:
                continue
            if url_pattern and url_pattern not in log.url:
                continue
            results.append(
                {
                    "method": log.method,
                    "url": log.url,
                    "status": log.response_status,
                    "duration_ms": log.duration_ms,
                    "timestamp": log.timestamp,
                }
            )
        return results

    def get_slow_requests(self, threshold_ms: float = 1000) -> list[dict]:
        return [
            {
                "method": l.method,
                "url": l.url,
                "duration_ms": l.duration_ms,
                "status": l.response_status,
            }
            for l in self._logs
            if l.duration_ms > threshold_ms
        ]

    def get_error_summary(self) -> dict:
        by_status = defaultdict(int)
        for log in self._logs:
            by_status[log.response_status] += 1
        return dict(by_status)

    def clear(self) -> None:
        self._logs.clear()

    def export_json(self) -> str:
        return json.dumps(
            [
                {
                    "method": l.method,
                    "url": l.url,
                    "status": l.response_status,
                    "duration_ms": l.duration_ms,
                    "timestamp": l.timestamp,
                }
                for l in self._logs
            ],
            indent=2,
        )


class StackTraceVisualizer:
    """3. Stack trace visualizer - formats and filters stack traces."""

    @staticmethod
    def capture() -> list[StackFrame]:
        frames = []
        for frame_info in inspect.stack()[1:]:
            ctx = inspect.getframeinfo(frame_info[0])
            code_context = ctx.code_context[0].strip() if ctx.code_context else None
            local_vars = {}
            try:
                local_vars = {
                    k: repr(v)[:200]
                    for k, v in frame_info[0].f_locals.items()
                }
            except Exception:
                pass
            frames.append(
                StackFrame(
                    filename=ctx.filename,
                    lineno=ctx.lineno,
                    name=frame_info.function,
                    code_context=code_context,
                    local_vars=local_vars,
                )
            )
        return frames

    @staticmethod
    def format(frames: list[StackFrame], show_vars: bool = False) -> str:
        lines = ["Stack Trace:", "=" * 60]
        for i, f in enumerate(frames):
            lines.append(f"  #{i} {f.name} at {f.filename}:{f.lineno}")
            if f.code_context:
                lines.append(f"    >> {f.code_context}")
            if show_vars and f.local_vars:
                for k, v in list(f.local_vars.items())[:5]:
                    lines.append(f"    {k} = {v}")
        return "\n".join(lines)

    @staticmethod
    def filter_framework(frames: list[StackFrame]) -> list[StackFrame]:
        known_frameworks = [
            "site-packages",
            "node_modules",
            "__pycache__",
            "lib/python",
        ]
        return [
            f
            for f in frames
            if not any(fw in f.filename for fw in known_frameworks)
        ]

    @staticmethod
    def get_last_n(frames: list[StackFrame], n: int) -> list[StackFrame]:
        return frames[:n]

    @staticmethod
    def format_exception(exc: Exception) -> str:
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        return "".join(tb)


class MemoryProfiler:
    """4. Memory profiler - tracks memory usage over time."""

    def __init__(self):
        self._samples: list[MemorySample] = []
        self._baseline: int | None = None
        self._tracking = False

    def _get_memory_info(self) -> dict:
        import os

        try:
            import psutil

            proc = psutil.Process(os.getpid())
            mem = proc.memory_info()
            return {
                "rss_bytes": mem.rss,
                "heap_bytes": getattr(mem, "heap", mem.rss),
            }
        except ImportError:
            return {"rss_bytes": 0, "heap_bytes": 0}

    def start(self) -> None:
        self._tracking = True
        info = self._get_memory_info()
        self._baseline = info["rss_bytes"]
        self.sample()

    def stop(self) -> None:
        self._tracking = False

    def sample(self) -> MemorySample:
        info = self._get_memory_info()
        obj_types = defaultdict(int)
        for obj in gc.get_objects():
            obj_types[type(obj).__name__] += 1
        top_types = dict(sorted(obj_types.items(), key=lambda x: -x[1])[:10])
        s = MemorySample(
            timestamp=time.time(),
            rss_bytes=info["rss_bytes"],
            heap_bytes=info["heap_bytes"],
            obj_count=sum(obj_types.values()),
            obj_types=top_types,
        )
        self._samples.append(s)
        return s

    def get_samples(self) -> list[dict]:
        return [
            {
                "timestamp": s.timestamp,
                "rss_mb": s.rss_bytes / (1024 * 1024),
                "heap_mb": s.heap_bytes / (1024 * 1024),
                "obj_count": s.obj_count,
            }
            for s in self._samples
        ]

    def get_growth(self) -> dict:
        if len(self._samples) < 2:
            return {"growth_bytes": 0, "growth_mb": 0}
        first = self._samples[0].rss_bytes
        last = self._samples[-1].rss_bytes
        return {
            "growth_bytes": last - first,
            "growth_mb": (last - first) / (1024 * 1024),
            "samples": len(self._samples),
        }

    def get_top_objects(self) -> dict:
        if not self._samples:
            return {}
        return self._samples[-1].obj_types

    def reset(self) -> None:
        self._samples.clear()
        self._baseline = None


class CPUProfiler:
    """5. CPU profiler - profiles function execution time."""

    def __init__(self):
        self._call_times: dict[str, list[float]] = defaultdict(list)
        self._call_counts: dict[str, int] = defaultdict(int)
        self._active_timers: dict[str, float] = {}

    def start(self, label: str = "default") -> None:
        self._active_timers[label] = time.perf_counter()

    def stop(self, label: str = "default") -> float:
        start = self._active_timers.pop(label, time.perf_counter())
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._call_times[label].append(elapsed_ms)
        self._call_counts[label] += 1
        return elapsed_ms

    def profile(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            label = f"{func.__module__}.{func.__qualname__}"
            self.start(label)
            try:
                return func(*args, **kwargs)
            finally:
                self.stop(label)

        return wrapper

    def get_results(self) -> CPUProfileResult:
        hotspots = []
        function_calls = []
        for label, times in self._call_times.items():
            total = sum(times)
            avg = total / len(times)
            entry = {
                "function": label,
                "total_ms": round(total, 3),
                "avg_ms": round(avg, 3),
                "min_ms": round(min(times), 3),
                "max_ms": round(max(times), 3),
                "call_count": self._call_counts[label],
            }
            function_calls.append(entry)
            hotspots.append(
                Hotspot(
                    function=label,
                    file="",
                    line=0,
                    cumulative_time_ms=total,
                    own_time_ms=avg,
                    call_count=self._call_counts[label],
                )
            )
        hotspots.sort(key=lambda h: h.cumulative_time_ms, reverse=True)
        total_time = sum(
            sum(times) for times in self._call_times.values()
        )
        return CPUProfileResult(
            total_time_ms=round(total_time, 3),
            function_calls=function_calls,
            hotspots=[
                {
                    "function": h.function,
                    "cumulative_ms": h.cumulative_time_ms,
                    "calls": h.call_count,
                }
                for h in hotspots[:10]
            ],
            call_counts=dict(self._call_counts),
        )

    def reset(self) -> None:
        self._call_times.clear()
        self._call_counts.clear()
        self._active_timers.clear()


class IOProfiler:
    """6. I/O profiler (disk/network)."""

    def __init__(self):
        self._samples: list[IOProfileSample] = []
        self._start_disk_read = 0
        self._start_disk_write = 0

    def start(self) -> None:
        import psutil

        io = psutil.disk_io_counters()
        self._start_disk_read = io.read_bytes if io else 0
        self._start_disk_write = io.write_bytes if io else 0

    def sample(self) -> IOProfileSample:
        import os

        try:
            import psutil

            disk = psutil.disk_io_counters()
            net = psutil.net_io_counters()
            open_fds = len(psutil.Process(os.getpid()).open_files())
        except ImportError:
            disk = None
            net = None
            open_fds = 0

        s = IOProfileSample(
            timestamp=time.time(),
            disk_read_bytes=disk.read_bytes if disk else 0,
            disk_write_bytes=disk.write_bytes if disk else 0,
            net_sent_bytes=net.bytes_sent if net else 0,
            net_recv_bytes=net.bytes_recv if net else 0,
            open_files=open_fds,
        )
        self._samples.append(s)
        return s

    def get_disk_usage(self) -> dict:
        if len(self._samples) < 2:
            return {"read_mb": 0, "write_mb": 0}
        first, last = self._samples[0], self._samples[-1]
        return {
            "read_mb": (last.disk_read_bytes - first.disk_read_bytes) / (1024 * 1024),
            "write_mb": (last.disk_write_bytes - first.disk_write_bytes) / (1024 * 1024),
        }

    def get_network_usage(self) -> dict:
        if len(self._samples) < 2:
            return {"sent_mb": 0, "recv_mb": 0}
        first, last = self._samples[0], self._samples[-1]
        return {
            "sent_mb": (last.net_sent_bytes - first.net_sent_bytes) / (1024 * 1024),
            "recv_mb": (last.net_recv_bytes - first.net_recv_bytes) / (1024 * 1024),
        }

    def get_file_handles(self) -> list[dict]:
        return [
            {"timestamp": s.timestamp, "open_files": s.open_files}
            for s in self._samples
        ]


class ThreadDeadlockDetector:
    """7. Thread deadlock detector."""

    def __init__(self):
        self._lock_graph: dict[str, set[str]] = defaultdict(set)
        self._lock_owners: dict[str, str] = {}
        self._deadlocks: list[DeadlockInfo] = []

    def register_lock(self, lock_id: str, owner_thread: str) -> None:
        self._lock_owners[lock_id] = owner_thread

    def register_wait(self, thread: str, waiting_for_lock: str) -> None:
        owner = self._lock_owners.get(waiting_for_lock)
        if owner and owner != thread:
            self._lock_graph[thread].add(owner)

    def detect(self) -> list[DeadlockInfo]:
        visited = set()
        path = []

        def dfs(node: str) -> list[str] | None:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:]
            if node in visited:
                return None
            path.append(node)
            for neighbor in self._lock_graph.get(node, []):
                result = dfs(neighbor)
                if result:
                    return result
            path.pop()
            visited.add(node)
            return None

        for node in list(self._lock_graph.keys()):
            result = dfs(node)
            if result:
                info = DeadlockInfo(
                    threads=result,
                    waiting_on={t: self._lock_graph.get(t, set()) for t in result},
                    detected_at=time.time(),
                )
                self._deadlocks.append(info)

        return self._deadlocks

    def get_results(self) -> list[dict]:
        return [
            {
                "threads": d.threads,
                "detected_at": d.detected_at,
                "severity": d.severity,
            }
            for d in self._deadlocks
        ]

    def reset(self) -> None:
        self._lock_graph.clear()
        self._lock_owners.clear()
        self._deadlocks.clear()


class ResourceLeakDetector:
    """8. Resource leak detector."""

    def __init__(self, leak_threshold_seconds: float = 60):
        self._open_resources: dict[str, dict] = {}
        self._leak_threshold = leak_threshold_seconds
        self._leaks: list[LeakCandidate] = []

    def open(self, resource_id: str, resource_type: str, description: str = "") -> None:
        self._open_resources[resource_id] = {
            "type": resource_type,
            "description": description,
            "opened_at": time.time(),
            "stack": "".join(traceback.format_stack()[:-1]),
        }

    def close(self, resource_id: str) -> None:
        self._open_resources.pop(resource_id, None)

    def scan(self) -> list[LeakCandidate]:
        now = time.time()
        self._leaks.clear()
        for _rid, info in self._open_resources.items():
            age = now - info["opened_at"]
            if age > self._leak_threshold:
                self._leaks.append(
                    LeakCandidate(
                        resource_type=info["type"],
                        description=info["description"],
                        age_seconds=age,
                        stack_trace=info["stack"],
                        severity="high" if age > 300 else "medium",
                    )
                )
        return self._leaks

    def get_open_count(self) -> dict:
        by_type = defaultdict(int)
        for info in self._open_resources.values():
            by_type[info["type"]] += 1
        return dict(by_type)

    def get_results(self) -> list[dict]:
        return [
            {
                "resource_type": l.resource_type,
                "description": l.description,
                "age_seconds": round(l.age_seconds, 1),
                "severity": l.severity,
            }
            for l in self._leaks
        ]


class PerformanceHotspotFinder:
    """9. Performance hotspot finder."""

    def __init__(self):
        self._metrics: dict[str, dict] = defaultdict(
            lambda: {"total_ms": 0, "count": 0, "max_ms": 0}
        )

    def record(self, function: str, duration_ms: float) -> None:
        m = self._metrics[function]
        m["total_ms"] += duration_ms
        m["count"] += 1
        m["max_ms"] = max(m["max_ms"], duration_ms)

    def find_hotspots(self, top_n: int = 10) -> list[Hotspot]:
        hotspots = []
        for func, m in self._metrics.items():
            hotspots.append(
                Hotspot(
                    function=func,
                    file="",
                    line=0,
                    cumulative_time_ms=m["total_ms"],
                    own_time_ms=m["total_ms"] / m["count"] if m["count"] else 0,
                    call_count=m["count"],
                )
            )
        hotspots.sort(key=lambda h: h.cumulative_time_ms, reverse=True)
        return hotspots[:top_n]

    def get_results(self) -> list[dict]:
        return [
            {
                "function": h.function,
                "cumulative_ms": round(h.cumulative_time_ms, 3),
                "avg_ms": round(h.own_time_ms, 3),
                "calls": h.call_count,
            }
            for h in self.find_hotspots()
        ]

    def reset(self) -> None:
        self._metrics.clear()


class DebugSessionReplay:
    """10. Debug session replays - records and replays execution traces."""

    def __init__(self):
        self._sessions: dict[str, list[ReplayEvent]] = {}
        self._active_session: str | None = None

    def start_session(self, session_id: str) -> str:
        if not session_id:
            session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
        self._sessions[session_id] = []
        self._active_session = session_id
        return session_id

    def record_event(self, event_type: str, data: dict) -> None:
        if not self._active_session:
            return
        self._sessions[self._active_session].append(
            ReplayEvent(
                timestamp=time.time(),
                event_type=event_type,
                data=data,
                session_id=self._active_session,
            )
        )

    def stop_session(self) -> list[dict]:
        session_id = self._active_session
        self._active_session = None
        return self.get_events(session_id)

    def get_events(self, session_id: str) -> list[dict]:
        events = self._sessions.get(session_id, [])
        if not events:
            return []
        base_ts = events[0].timestamp
        return [
            {
                "offset_ms": round((e.timestamp - base_ts) * 1000, 2),
                "type": e.event_type,
                "data": e.data,
            }
            for e in events
        ]

    def get_sessions(self) -> list[str]:
        return list(self._sessions.keys())

    def replay(self, session_id: str) -> list[dict]:
        return self.get_events(session_id)

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

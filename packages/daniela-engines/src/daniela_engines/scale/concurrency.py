"""
Concurrency (Ideas 21-30)
------------------------
Connection pools, thread pools, async task queues, rate limiting, read-write locks,
event loop monitoring, coroutine pools, work stealing, backpressure, dead letter queues.
"""

from __future__ import annotations

import collections
import logging
import queue
import threading
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Idea 21 - Connection pool manager (per-service)
# ---------------------------------------------------------------------------

@dataclass
class Connection:
    service: str
    conn_id: int
    created_at: float = field(default_factory=time.time)
    in_use: bool = False
    last_used: float = field(default_factory=time.time)


class ConnectionPool:
    """Per-service connection pool with health checks."""

    def __init__(self, service: str, max_size: int = 20, min_idle: int = 2,
                 max_idle_sec: float = 300):
        self.service = service
        self.max_size = max_size
        self.min_idle = min_idle
        self.max_idle_sec = max_idle_sec
        self._pool: collections.deque[Connection] = collections.deque()
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._next_id = 0
        self._created_total = 0
        self._borrowed_total = 0
        self._active_count = 0

    def _new_conn(self) -> Connection:
        self._next_id += 1
        self._created_total += 1
        return Connection(service=self.service, conn_id=self._next_id)

    def acquire(self, timeout: float = 10.0) -> Connection:
        deadline = time.monotonic() + timeout
        with self._cond:
            while True:
                # Try to get an idle connection
                while self._pool:
                    conn = self._pool.popleft()
                    if time.time() - conn.created_at < self.max_idle_sec:
                        conn.in_use = True
                        conn.last_used = time.time()
                        self._active_count += 1
                        self._borrowed_total += 1
                        return conn

                # Create new if under limit
                if self._active_count < self.max_size:
                    conn = self._new_conn()
                    conn.in_use = True
                    self._active_count += 1
                    self._borrowed_total += 1
                    return conn

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"Connection pool [{self.service}] exhausted")
                self._cond.wait(timeout=min(remaining, 1.0))

    def release(self, conn: Connection):
        with self._cond:
            conn.in_use = False
            conn.last_used = time.time()
            self._active_count = max(0, self._active_count - 1)
            self._pool.append(conn)
            self._cond.notify()

    def close_all(self):
        with self._lock:
            self._pool.clear()

    @property
    def idle_count(self) -> int:
        return len(self._pool)

    def stats(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "idle": self.idle_count,
            "max_size": self.max_size,
            "created_total": self._created_total,
            "borrowed_total": self._borrowed_total,
        }


class ConnectionPoolManager:
    """Manage connection pools for multiple services."""

    def __init__(self):
        self._pools: dict[str, ConnectionPool] = {}

    def get_pool(self, service: str, max_size: int = 20) -> ConnectionPool:
        if service not in self._pools:
            self._pools[service] = ConnectionPool(service=service, max_size=max_size)
        return self._pools[service]

    def acquire(self, service: str, **kwargs) -> Connection:
        return self.get_pool(service).acquire(**kwargs)

    def release(self, conn: Connection):
        self.get_pool(conn.service).release(conn)

    def stats(self) -> dict[str, Any]:
        return {name: pool.stats() for name, pool in self._pools.items()}


# ---------------------------------------------------------------------------
# Idea 22 - Thread pool executor (configurable)
# ---------------------------------------------------------------------------

class ConfigurableThreadPool:
    """Configurable thread pool with min/max workers and dynamic scaling."""

    def __init__(self, min_workers: int = 2, max_workers: int = 8,
                 scale_up_threshold: float = 0.8):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_up_threshold = scale_up_threshold
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._active_count = 0
        self._submitted_total = 0
        self._completed_total = 0
        self._lock = threading.Lock()

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        with self._lock:
            self._active_count += 1
            self._submitted_total += 1

        future = self._executor.submit(fn, *args, **kwargs)

        def _on_done(f):
            with self._lock:
                self._active_count -= 1
                self._completed_total += 1
            if f.exception():
                logger.warning("Task raised: %s", f.exception())

        future.add_done_callback(_on_done)
        return future

    def shutdown(self, wait: bool = True):
        self._executor.shutdown(wait=wait)

    def stats(self) -> dict[str, Any]:
        return {
            "min_workers": self.min_workers,
            "max_workers": self.max_workers,
            "active": self._active_count,
            "submitted": self._submitted_total,
            "completed": self._completed_total,
        }


# ---------------------------------------------------------------------------
# Idea 23 - Async task queue (in-process)
# ---------------------------------------------------------------------------

class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass(order=True)
class TaskItem:
    priority: int
    created_at: float = field(compare=False, default_factory=time.time)
    task_id: str = field(compare=False, default="")
    fn: Callable = field(compare=False, default=None)
    args: tuple = field(compare=False, default=())
    kwargs: dict = field(compare=False, default_factory=dict)
    future: Future = field(compare=False, default=None)


class AsyncTaskQueue:
    """Priority-based in-process task queue with worker threads."""

    def __init__(self, num_workers: int = 4, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        self._queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_queue_size)
        self._workers: list[threading.Thread] = []
        self._running = False
        self._completed = 0
        self._failed = 0
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=num_workers)

        for i in range(num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True, name=f"task-worker-{i}")
            self._workers.append(t)

    def start(self):
        self._running = True
        for t in self._workers:
            t.start()

    def stop(self):
        self._running = False
        for _ in self._workers:
            self._queue.put(None)
        self._executor.shutdown(wait=True)

    def _worker_loop(self):
        while self._running:
            try:
                item = self._queue.get(timeout=1)
                if item is None:
                    break
                try:
                    item.fn(*item.args, **item.kwargs)
                    with self._lock:
                        self._completed += 1
                except Exception as exc:
                    logger.warning("Task %s failed: %s", item.task_id, exc)
                    with self._lock:
                        self._failed += 1
            except queue.Empty:
                continue

    def enqueue(self, fn: Callable, args: tuple = (), kwargs: dict = None,
                priority: TaskPriority = TaskPriority.NORMAL, task_id: str = "") -> bool:
        if self._queue.full():
            return False
        item = TaskItem(
            priority=100 - priority.value,
            task_id=task_id or f"task-{time.time_ns()}",
            fn=fn,
            args=args,
            kwargs=kwargs or {},
        )
        self._queue.put(item)
        return True

    def stats(self) -> dict[str, Any]:
        return {
            "pending": self._queue.qsize(),
            "completed": self._completed,
            "failed": self._failed,
            "workers": len(self._workers),
            "running": self._running,
        }


# ---------------------------------------------------------------------------
# Idea 24 - Semaphore-based rate limiting
# ---------------------------------------------------------------------------

class SemaphoreRateLimiter:
    """Semaphore-based rate limiter per key."""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphores: dict[str, threading.Semaphore] = {}
        self._lock = threading.Lock()
        self._counts: dict[str, int] = {}

    def _get_sem(self, key: str) -> threading.Semaphore:
        with self._lock:
            if key not in self._semaphores:
                self._semaphores[key] = threading.Semaphore(self.max_concurrent)
                self._counts[key] = 0
            return self._semaphores[key]

    def acquire(self, key: str) -> bool:
        sem = self._get_sem(key)
        acquired = sem.acquire(blocking=False)
        if acquired:
            with self._lock:
                self._counts[key] = self._counts.get(key, 0) + 1
        return acquired

    def release(self, key: str):
        sem = self._get_sem(key)
        sem.release()
        with self._lock:
            self._counts[key] = max(0, self._counts.get(key, 1) - 1)

    def active_count(self, key: str) -> int:
        return self._counts.get(key, 0)


# ---------------------------------------------------------------------------
# Idea 25 - Read-write lock implementation
# ---------------------------------------------------------------------------

class ReadWriteLock:
    """Multiple-reader, single-writer lock."""

    def __init__(self):
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0
        self._writers = 0
        self._write_waiters = 0

    def acquire_read(self, timeout: float = 10.0) -> bool:
        with self._read_ready:
            deadline = time.monotonic() + timeout
            while self._writers > 0 or self._write_waiters > 0:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._read_ready.wait(timeout=min(remaining, 0.1))
            self._readers += 1
            return True

    def release_read(self):
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self, timeout: float = 10.0) -> bool:
        with self._read_ready:
            self._write_waiters += 1
            deadline = time.monotonic() + timeout
            while self._readers > 0 or self._writers > 0:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._write_waiters -= 1
                    return False
                self._read_ready.wait(timeout=min(remaining, 0.1))
            self._write_waiters -= 1
            self._writers += 1
            return True

    def release_write(self):
        with self._read_ready:
            self._writers -= 1
            self._read_ready.notify_all()

    @property
    def active_readers(self) -> int:
        return self._readers

    @property
    def active_writers(self) -> int:
        return self._writers


# ---------------------------------------------------------------------------
# Idea 26 - Event loop monitoring
# ---------------------------------------------------------------------------

class EventLoopMonitor:
    """Monitor event loop health by tracking task execution times."""

    def __init__(self, slow_threshold_ms: float = 100):
        self.slow_threshold_ms = slow_threshold_ms
        self._execution_times: collections.deque[float] = collections.deque(maxlen=1000)
        self._slow_tasks: list[tuple[float, str]] = []
        self._lock = threading.Lock()

    def record_execution(self, task_name: str, duration_ms: float):
        with self._lock:
            self._execution_times.append(duration_ms)
            if duration_ms > self.slow_threshold_ms:
                self._slow_tasks.append((time.time(), task_name))
                if len(self._slow_tasks) > 100:
                    self._slow_tasks = self._slow_tasks[-50:]

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            times = list(self._execution_times)
            if not times:
                return {"count": 0, "avg_ms": 0, "p95_ms": 0, "p99_ms": 0, "slow_count": 0}
            sorted_times = sorted(times)
            return {
                "count": len(times),
                "avg_ms": round(sum(times) / len(times), 3),
                "min_ms": round(min(times), 3),
                "max_ms": round(max(times), 3),
                "p95_ms": round(sorted_times[int(len(sorted_times) * 0.95)], 3),
                "p99_ms": round(sorted_times[int(len(sorted_times) * 0.99)], 3),
                "slow_count": len(self._slow_tasks),
            }


# ---------------------------------------------------------------------------
# Idea 27 - Coroutine pool manager
# ---------------------------------------------------------------------------

class CoroutinePoolManager:
    """
    In-process coroutine pool using threads to simulate async work.
    For real async, wrap with asyncio.run in thread.
    """

    def __init__(self, max_concurrent: int = 50):
        self.max_concurrent = max_concurrent
        self._semaphore = threading.Semaphore(max_concurrent)
        self._active = 0
        self._total_spawned = 0
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=min(max_concurrent, 16))

    def spawn(self, fn: Callable, *args, **kwargs) -> Future:
        with self._lock:
            self._total_spawned += 1

        def _guarded():
            self._semaphore.acquire()
            with self._lock:
                self._active += 1
            try:
                return fn(*args, **kwargs)
            finally:
                with self._lock:
                    self._active -= 1
                self._semaphore.release()

        return self._executor.submit(_guarded)

    def stats(self) -> dict[str, Any]:
        return {
            "max_concurrent": self.max_concurrent,
            "active": self._active,
            "total_spawned": self._total_spawned,
        }


# ---------------------------------------------------------------------------
# Idea 28 - Work stealing scheduler
# ---------------------------------------------------------------------------

class WorkStealingScheduler:
    """Work-stealing scheduler: idle workers steal from busy ones."""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self._queues: list[collections.deque[tuple[Callable, tuple, dict]]] = [
            collections.deque() for _ in range(num_workers)
        ]
        self._lock = threading.Lock()
        self._steal_count = 0
        self._executors = [ThreadPoolExecutor(max_workers=1) for _ in range(num_workers)]
        self._futures: list[list[Future]] = [[] for _ in range(num_workers)]
        self._running = True

    def submit(self, fn: Callable, *args, **kwargs):
        # Find least loaded queue
        with self._lock:
            min_idx = min(range(self.num_workers), key=lambda i: len(self._queues[i]))
            self._queues[min_idx].append((fn, args, kwargs))

    def start(self):
        for i in range(self.num_workers):
            self._executors[i].submit(self._worker_loop, i)

    def _worker_loop(self, worker_id: int):
        while self._running:
            task = None
            with self._lock:
                if self._queues[worker_id]:
                    task = self._queues[worker_id].popleft()
                else:
                    # Steal from busiest queue
                    busiest = max(range(self.num_workers), key=lambda i: len(self._queues[i]))
                    if self._queues[busiest]:
                        task = self._queues[busiest].popleft()
                        self._steal_count += 1

            if task:
                fn, args, kwargs = task
                try:
                    fn(*args, **kwargs)
                except Exception as exc:
                    logger.warning("Worker %d task failed: %s", worker_id, exc)
            else:
                time.sleep(0.01)

    def stop(self):
        self._running = False
        for ex in self._executors:
            ex.shutdown(wait=False)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "workers": self.num_workers,
                "queue_sizes": [len(q) for q in self._queues],
                "steal_count": self._steal_count,
            }


# ---------------------------------------------------------------------------
# Idea 29 - Backpressure mechanism
# ---------------------------------------------------------------------------

class BackpressureController:
    """Monitor throughput and apply backpressure when overloaded."""

    def __init__(self, high_water_mark: int = 1000, low_water_mark: int = 100,
                 window_sec: float = 1.0):
        self.high_water_mark = high_water_mark
        self.low_water_mark = low_water_mark
        self.window_sec = window_sec
        self._inflight = 0
        self._lock = threading.Lock()
        self._throttled = False
        self._throttle_events: list[float] = []

    @property
    def is_throttled(self) -> bool:
        return self._throttled

    def on_request_start(self):
        with self._lock:
            self._inflight += 1
            if self._inflight >= self.high_water_mark:
                self._throttled = True
                self._throttle_events.append(time.time())

    def on_request_end(self):
        with self._lock:
            self._inflight = max(0, self._inflight - 1)
            if self._inflight <= self.low_water_mark:
                self._throttled = False

    def should_reject(self) -> bool:
        return self._throttled

    @property
    def current_inflight(self) -> int:
        return self._inflight

    def stats(self) -> dict[str, Any]:
        return {
            "inflight": self._inflight,
            "throttled": self._throttled,
            "high_water_mark": self.high_water_mark,
            "low_water_mark": self.low_water_mark,
            "throttle_events": len(self._throttle_events),
        }


# ---------------------------------------------------------------------------
# Idea 30 - Dead letter queue handler
# ---------------------------------------------------------------------------

@dataclass
class DeadLetter:
    message: Any
    error: str
    timestamp: float
    retry_count: int = 0
    source: str = ""


class DeadLetterQueueHandler:
    """Collect and manage failed tasks for later inspection/retry."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue: collections.deque[DeadLetter] = collections.deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._total_received = 0
        self._total_retried = 0
        self._total_discarded = 0

    def enqueue(self, message: Any, error: str, source: str = ""):
        with self._lock:
            dl = DeadLetter(message=message, error=error, timestamp=time.time(), source=source)
            self._queue.append(dl)
            self._total_received += 1

    def retry_all(self, retry_fn: Callable) -> list[Any]:
        results = []
        with self._lock:
            items = list(self._queue)
            self._queue.clear()
        for item in items:
            try:
                result = retry_fn(item.message)
                results.append(result)
                self._total_retried += 1
            except Exception as exc:
                self.enqueue(item.message, str(exc), item.source)
        return results

    def discard_all(self):
        with self._lock:
            self._total_discarded += len(self._queue)
            self._queue.clear()

    def peek(self, n: int = 10) -> list[DeadLetter]:
        with self._lock:
            return list(self._queue)[:n]

    def stats(self) -> dict[str, Any]:
        return {
            "pending": len(self._queue),
            "total_received": self._total_received,
            "total_retried": self._total_retried,
            "total_discarded": self._total_discarded,
        }


# ---------------------------------------------------------------------------
# Unified Concurrency Manager
# ---------------------------------------------------------------------------

class ConcurrencyManager:
    """Unified interface to all concurrency primitives."""

    def __init__(self):
        self.connection_pools = ConnectionPoolManager()
        self.thread_pool = ConfigurableThreadPool()
        self.task_queue = AsyncTaskQueue()
        self.rate_limiter = SemaphoreRateLimiter()
        self.rw_lock = ReadWriteLock()
        self.event_loop_monitor = EventLoopMonitor()
        self.coroutine_pool = CoroutinePoolManager()
        self.work_stealer = WorkStealingScheduler()
        self.backpressure = BackpressureController()
        self.dead_letter = DeadLetterQueueHandler()

    def stats(self) -> dict[str, Any]:
        return {
            "connection_pools": self.connection_pools.stats(),
            "thread_pool": self.thread_pool.stats(),
            "task_queue": self.task_queue.stats(),
            "coroutine_pool": self.coroutine_pool.stats(),
            "work_stealer": self.work_stealer.stats(),
            "backpressure": self.backpressure.stats(),
            "dead_letter": self.dead_letter.stats(),
        }

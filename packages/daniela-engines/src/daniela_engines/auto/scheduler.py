"""
Task scheduler (Ideas 11-20).
Cron parser, one-shot tasks, recurring tasks, priority queues,
rate limiting, distributed locking, dependency resolution, and more.
"""

import logging
import sqlite3
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    WAITING = "waiting"


class RecurrenceType(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"
    INTERVAL = "interval"


@dataclass
class ScheduledJob:
    job_id: str
    name: str
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)
    recurrence: RecurrenceType = RecurrenceType.ONCE
    cron_expression: str | None = None
    interval_seconds: int | None = None
    next_run: float | None = None
    last_run: float | None = None
    priority: int = 0
    status: JobStatus = JobStatus.PENDING
    max_retries: int = 3
    retry_count: int = 0
    depends_on: list[str] = field(default_factory=list)
    rate_limit_per_minute: int | None = None
    calendar_aware: bool = False
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["recurrence"] = self.recurrence.value
        d["status"] = self.status.value
        return d


class CronExpression:
    """Idea 11: Cron expression parser."""

    def __init__(self, expression: str):
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError("Cron must have 5 parts: minute hour day month weekday")
        self.minute = self._parse_field(parts[0], 0, 59)
        self.hour = self._parse_field(parts[1], 0, 23)
        self.day = self._parse_field(parts[2], 1, 31)
        self.month = self._parse_field(parts[3], 1, 12)
        self.weekday = self._parse_field(parts[4], 0, 6)

    def _parse_field(self, field_str: str, min_val: int, max_val: int) -> set[int]:
        values = set()
        for part in field_str.split(","):
            if part == "*":
                values.update(range(min_val, max_val + 1))
            elif "-" in part:
                start, end = part.split("-", 1)
                values.update(range(int(start), int(end) + 1))
            elif "/" in part:
                start, step = part.split("/", 1)
                start_val = int(start) if start.isdigit() else min_val
                values.update(range(start_val, max_val + 1, int(step)))
            else:
                values.add(int(part))
        return values

    def matches(self, dt: datetime | None = None) -> bool:
        if dt is None:
            dt = datetime.now()
        return (dt.minute in self.minute and dt.hour in self.hour and
                dt.day in self.day and dt.month in self.month and
                dt.weekday() in self.weekday)

    def next_run(self, after: datetime | None = None) -> datetime:
        if after is None:
            after = datetime.now()
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        for _ in range(525600):
            if self.matches(candidate):
                return candidate
            candidate += timedelta(minutes=1)
        return after + timedelta(days=365)


class DistributedLock:
    """Idea 16: Distributed locking via SQLite."""

    def __init__(self, db_path: str = "scheduler_locks.db"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self._conn.execute("""CREATE TABLE IF NOT EXISTS locks (
            lock_key TEXT PRIMARY KEY, owner TEXT,
            acquired_at REAL, expires_at REAL)""")
        self._conn.commit()

    def acquire(self, lock_key: str, owner: str, ttl: float = 60.0) -> bool:
        with self._conn:
            now = time.time()
            self._conn.execute("DELETE FROM locks WHERE expires_at < ?", (now,))
            existing = self._conn.execute(
                "SELECT owner FROM locks WHERE lock_key = ?", (lock_key,)
            ).fetchone()
            if existing is None:
                self._conn.execute("INSERT INTO locks VALUES (?, ?, ?, ?)",
                             (lock_key, owner, now, now + ttl))
                return True
            elif existing[0] == owner:
                self._conn.execute("UPDATE locks SET expires_at = ? WHERE lock_key = ?",
                             (now + ttl, lock_key))
                return True
            return False

    def release(self, lock_key: str, owner: str):
        with self._conn:
            self._conn.execute("DELETE FROM locks WHERE lock_key = ? AND owner = ?",
                         (lock_key, owner))

    def is_locked(self, lock_key: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM locks WHERE lock_key = ? AND expires_at > ?",
            (lock_key, time.time()),
        ).fetchone()
        return row is not None


class RateLimiter:
    """Idea 15: Rate limiting per task type."""

    def __init__(self):
        self._windows: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, task_type: str, max_per_minute: int) -> bool:
        with self._lock:
            now = time.time()
            window = self._windows.setdefault(task_type, [])
            window[:] = [t for t in window if now - t < 60.0]
            if len(window) < max_per_minute:
                window.append(now)
                return True
            return False

    def wait_time(self, task_type: str, max_per_minute: int) -> float:
        with self._lock:
            now = time.time()
            window = self._windows.get(task_type, [])
            window = [t for t in window if now - t < 60.0]
            if len(window) < max_per_minute:
                return 0.0
            return 60.0 - (now - window[0])


class CalendarAwareScheduler:
    """Idea 19: Calendar-aware scheduling."""

    HOLIDAYS_2026 = {
        "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25",
        "2026-07-04", "2026-09-07", "2026-11-26", "2026-12-25",
    }

    @staticmethod
    def is_weekend(dt: datetime) -> bool:
        return dt.weekday() >= 5

    @classmethod
    def is_holiday(cls, dt: datetime) -> bool:
        return dt.strftime("%Y-%m-%d") in cls.HOLIDAYS_2026

    @classmethod
    def is_business_day(cls, dt: datetime) -> bool:
        return not cls.is_weekend(dt) and not cls.is_holiday(dt)

    @classmethod
    def next_business_day(cls, dt: datetime) -> datetime:
        next_day = dt + timedelta(days=1)
        while not cls.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    @classmethod
    def skip_holidays(cls, dt: datetime) -> datetime:
        while cls.is_holiday(dt) or cls.is_weekend(dt):
            dt += timedelta(days=1)
        return dt


class TaskScheduler:
    """Task scheduler (Ideas 11-20)."""

    def __init__(self, action_handlers: dict[str, Callable] | None = None):
        self.jobs: dict[str, ScheduledJob] = {}
        self.action_handlers = action_handlers or {}
        self.lock = DistributedLock()
        self.rate_limiter = RateLimiter()
        self.calendar = CalendarAwareScheduler()
        self._running = False
        self._thread: threading.Thread | None = None
        self._history: list[dict[str, Any]] = []

    def register_action(self, action_type: str, handler: Callable):
        self.action_handlers[action_type] = handler

    def add_job(self, name: str, action_type: str, params: dict | None = None,
                recurrence: str = "once", cron_expr: str | None = None,
                interval_seconds: int | None = None, priority: int = 0,
                depends_on: list[str] | None = None,
                rate_limit: int | None = None,
                calendar_aware: bool = False, tags: list[str] | None = None) -> ScheduledJob:
        job = ScheduledJob(
            job_id=str(uuid.uuid4()), name=name, action_type=action_type,
            params=params or {}, recurrence=RecurrenceType(recurrence),
            cron_expression=cron_expr, interval_seconds=interval_seconds,
            priority=priority, depends_on=depends_on or [],
            rate_limit_per_minute=rate_limit, calendar_aware=calendar_aware,
            tags=tags or [],
        )
        if recurrence == "once":
            job.next_run = time.time() + (interval_seconds or 0)
        elif recurrence == "cron" and cron_expr:
            job.next_run = CronExpression(cron_expr).next_run().timestamp()
        elif recurrence == "daily":
            job.next_run = time.time() + 86400
        elif recurrence == "weekly":
            job.next_run = time.time() + 604800
        elif recurrence == "monthly":
            job.next_run = time.time() + 2592000
        self.jobs[job.job_id] = job
        return job

    def remove_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False

    def pause_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if job:
            job.status = JobStatus.PAUSED
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if job and job.status == JobStatus.PAUSED:
            job.status = JobStatus.PENDING
            return True
        return False

    def get_job(self, job_id: str) -> ScheduledJob | None:
        return self.jobs.get(job_id)

    def list_jobs(self, status: str | None = None,
                  tags: list[str] | None = None) -> list[dict]:
        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j.status.value == status]
        if tags:
            jobs = [j for j in jobs if any(t in j.tags for t in tags)]
        return [j.to_dict() for j in jobs]

    def _resolve_dependencies(self, job: ScheduledJob) -> bool:
        for dep_id in job.depends_on:
            dep = self.jobs.get(dep_id)
            if dep and dep.status != JobStatus.COMPLETED:
                return False
        return True

    def _schedule_next(self, job: ScheduledJob):
        now = time.time()
        if job.recurrence == RecurrenceType.ONCE:
            job.status = JobStatus.COMPLETED
            job.next_run = None
        elif job.recurrence == RecurrenceType.INTERVAL and job.interval_seconds:
            job.next_run = now + job.interval_seconds
            job.status = JobStatus.PENDING
        elif job.recurrence == RecurrenceType.CRON and job.cron_expression:
            job.next_run = CronExpression(job.cron_expression).next_run().timestamp()
            job.status = JobStatus.PENDING
        elif job.recurrence == RecurrenceType.DAILY:
            job.next_run = now + 86400
            job.status = JobStatus.PENDING
        elif job.recurrence == RecurrenceType.WEEKLY:
            job.next_run = now + 604800
            job.status = JobStatus.PENDING
        elif job.recurrence == RecurrenceType.MONTHLY:
            job.next_run = now + 2592000
            job.status = JobStatus.PENDING

    def execute_job(self, job_id: str) -> dict[str, Any]:
        job = self.jobs.get(job_id)
        if not job:
            return {"error": "Job not found"}

        lock_key = f"job_lock_{job.job_id}"
        owner = f"executor_{uuid.uuid4().hex[:8]}"

        if not self.lock.acquire(lock_key, owner, ttl=300):
            return {"job_id": job.job_id, "status": "skipped", "reason": "locked"}

        try:
            if not self._resolve_dependencies(job):
                return {"job_id": job.job_id, "status": "skipped", "reason": "deps_not_met"}

            if job.rate_limit_per_minute and not self.rate_limiter.allow(
                job.action_type, job.rate_limit_per_minute
            ):
                return {"job_id": job.job_id, "status": "skipped", "reason": "rate_limited"}

            if job.calendar_aware:
                now = datetime.now()
                if not self.calendar.is_business_day(now):
                    job.next_run = self.calendar.next_business_day(now).timestamp()
                    return {"job_id": job.job_id, "status": "deferred", "reason": "holiday"}

            handler = self.action_handlers.get(job.action_type)
            if not handler:
                job.status = JobStatus.FAILED
                return {"job_id": job.job_id, "status": "failed", "reason": "no_handler"}

            job.status = JobStatus.RUNNING
            job.last_run = time.time()

            try:
                result = handler(job.params)
                job.status = JobStatus.COMPLETED
                job.retry_count = 0
                self._schedule_next(job)
                entry = {"job_id": job.job_id, "status": "completed", "result": str(result),
                         "timestamp": time.time()}
                self._history.append(entry)
                return entry
            except Exception as e:
                job.retry_count += 1
                if job.retry_count <= job.max_retries:
                    job.status = JobStatus.PENDING
                    job.next_run = time.time() + (30 * (2 ** (job.retry_count - 1)))
                    return {"job_id": job.job_id, "status": "retrying",
                            "attempt": job.retry_count}
                else:
                    job.status = JobStatus.FAILED
                    entry = {"job_id": job.job_id, "status": "failed", "error": str(e),
                             "timestamp": time.time()}
                    self._history.append(entry)
                    return entry
        finally:
            self.lock.release(lock_key, owner)

    def execute_ready_jobs(self) -> list[dict[str, Any]]:
        now = time.time()
        results = []
        ready_jobs = sorted(
            [j for j in self.jobs.values()
             if j.enabled and j.status in (JobStatus.PENDING, JobStatus.WAITING)
             and j.next_run and j.next_run <= now],
            key=lambda j: (-j.priority, j.next_run or 0),
        )
        for job in ready_jobs:
            result = self.execute_job(job.job_id)
            results.append(result)
        return results

    def get_history(self, job_id: str | None = None) -> list[dict]:
        if job_id:
            return [h for h in self._history if h.get("job_id") == job_id]
        return list(self._history)

    def add_batch(self, jobs_data: list[dict[str, Any]]) -> list[ScheduledJob]:
        created = []
        for jd in jobs_data:
            job = self.add_job(
                name=jd["name"], action_type=jd["action_type"],
                params=jd.get("params"), recurrence=jd.get("recurrence", "once"),
                cron_expr=jd.get("cron_expr"), priority=jd.get("priority", 0),
                depends_on=jd.get("depends_on"), tags=jd.get("tags"),
            )
            created.append(job)
        return created

"""
Event Store for aig - Event Sourcing with SQLite backend.

Provides append-only event storage with versioning, snapshots, and projections.
"""

import json
import os
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.event_bus import Event
from core.paths import REPO_ROOT


@dataclass
class StoredEvent:
    """Event as stored in the event store."""
    id: int
    stream: str
    version: int
    event_type: str
    event_id: str
    aggregate_id: str
    aggregate_type: str
    payload: dict[str, Any]
    metadata: dict[str, Any]
    timestamp: str

    def to_event(self) -> 'Event':
        return Event(
            event_type=self.event_type,
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            payload=self.payload,
            event_id=self.event_id,
            version=self.version,
            timestamp=self.timestamp,
            metadata=self.metadata
        )


@dataclass
class Snapshot:
    """Aggregate snapshot for faster reconstruction."""
    id: int
    aggregate_id: str
    aggregate_type: str
    version: int
    state: dict[str, Any]
    timestamp: str


class EventStore:
    """
    SQLite-based event store with:
    - Append-only event storage
    - Optimistic concurrency control (version checking)
    - Snapshots for fast aggregate reconstruction
    - Stream subscriptions for projections
    - Correlation/causation ID tracking
    """

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = os.path.join(REPO_ROOT, "data", "event_store.db")

        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    @contextmanager
    def _get_conn(self) -> Iterator[sqlite3.Connection]:
        """Thread-local connection with row factory."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA busy_timeout = 5000")
            self._local.conn = conn

        yield self._local.conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_conn() as conn:
            conn.executescript("""
                -- Events table
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL,
                    correlation_id TEXT,
                    causation_id TEXT,
                    UNIQUE(stream, version)
                );

                CREATE INDEX IF NOT EXISTS idx_events_stream_version
                    ON events(stream, version);
                CREATE INDEX IF NOT EXISTS idx_events_aggregate
                    ON events(aggregate_id, aggregate_type);
                CREATE INDEX IF NOT EXISTS idx_events_correlation
                    ON events(correlation_id);
                CREATE INDEX IF NOT EXISTS idx_events_causation
                    ON events(causation_id);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp
                    ON events(timestamp DESC);

                -- Snapshots table
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aggregate_id TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    UNIQUE(aggregate_id, aggregate_type, version)
                );

                CREATE INDEX IF NOT EXISTS idx_snapshots_aggregate
                    ON snapshots(aggregate_id, aggregate_type);

                -- Projections checkpoint table
                CREATE TABLE IF NOT EXISTS projection_checkpoints (
                    projection_name TEXT PRIMARY KEY,
                    stream TEXT NOT NULL,
                    last_version INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );

                -- Dead letter queue for failed event processing
                CREATE TABLE IF NOT EXISTS dead_letters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    event_data TEXT NOT NULL,
                    error TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_attempt TEXT
                );
            """)

    # ─── Event Storage ───

    def append(
        self,
        stream: str,
        events: list[Event],
        expected_version: int | None = None
    ) -> int:
        """
        Append events to stream with optimistic concurrency.

        Args:
            stream: Stream name (e.g., "User-123")
            events: Events to append
            expected_version: Expected current version (None = no check)

        Returns:
            New version number

        Raises:
            ConcurrencyError: If version mismatch
        """
        if not events:
            return self.get_version(stream)

        with self._get_conn() as conn:
            # Check current version
            current_version = self.get_version(stream)
            if expected_version is not None and current_version != expected_version:
                raise ConcurrencyError(
                    f"Version conflict: expected {expected_version}, got {current_version}"
                )

            # Verify sequential versions
            for i, event in enumerate(events):
                if event.version != current_version + i + 1:
                    raise ValueError(
                        f"Event version {event.version} != expected {current_version + i + 1}"
                    )

            # Insert events
            datetime.utcnow().isoformat() + "Z"
            for event in events:
                conn.execute("""
                    INSERT INTO events (
                        stream, version, event_type, event_id,
                        aggregate_id, aggregate_type, payload, metadata,
                        timestamp, correlation_id, causation_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stream, event.version, event.event_type, event.event_id,
                    event.aggregate_id, event.aggregate_type,
                    json.dumps(event.payload), json.dumps(event.metadata),
                    event.timestamp,
                    event.metadata.get("correlation_id"),
                    event.metadata.get("causation_id")
                ))

            conn.commit()
            return events[-1].version

    def read_stream(
        self,
        stream: str,
        from_version: int = 0,
        limit: int | None = None
    ) -> list[Event]:
        """Read events from stream."""
        with self._get_conn() as conn:
            query = """
                SELECT * FROM events
                WHERE stream = ? AND version > ?
                ORDER BY version
            """
            params = [stream, from_version]
            if limit:
                query += " LIMIT ?"
                params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_event(row) for row in rows]

    def read_aggregate(
        self,
        aggregate_id: str,
        aggregate_type: str,
        from_version: int = 0
    ) -> list[Event]:
        """Read all events for an aggregate."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM events
                WHERE aggregate_id = ? AND aggregate_type = ? AND version > ?
                ORDER BY version
            """, (aggregate_id, aggregate_type, from_version)).fetchall()
            return [self._row_to_event(row) for row in rows]

    def get_version(self, stream: str) -> int:
        """Get current version of stream."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT MAX(version) as v FROM events WHERE stream = ?",
                (stream,)
            ).fetchone()
            return row["v"] if row and row["v"] is not None else 0

    def get_events_by_correlation(self, correlation_id: str) -> list[Event]:
        """Get all events with given correlation ID."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE correlation_id = ? ORDER BY version",
                (correlation_id,)
            ).fetchall()
            return [self._row_to_event(row) for row in rows]

    def get_events_by_causation(self, causation_id: str) -> list[Event]:
        """Get all events caused by given event."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE causation_id = ? ORDER BY version",
                (causation_id,)
            ).fetchall()
            return [self._row_to_event(row) for row in rows]

    # ─── Snapshots ───

    SNAPSHOT_INTERVAL = 100

    def save_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: int,
        state: dict[str, Any]
    ) -> None:
        """Save aggregate snapshot."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO snapshots
                (aggregate_id, aggregate_type, version, state, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                aggregate_id, aggregate_type, version,
                json.dumps(state), datetime.utcnow().isoformat() + "Z"
            ))
            conn.commit()

    def get_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        max_version: int | None = None
    ) -> Snapshot | None:
        """Get latest snapshot for aggregate."""
        with self._get_conn() as conn:
            if max_version:
                row = conn.execute("""
                    SELECT * FROM snapshots
                    WHERE aggregate_id = ? AND aggregate_type = ? AND version <= ?
                    ORDER BY version DESC LIMIT 1
                """, (aggregate_id, aggregate_type, max_version)).fetchone()
            else:
                row = conn.execute("""
                    SELECT * FROM snapshots
                    WHERE aggregate_id = ? AND aggregate_type = ?
                    ORDER BY version DESC LIMIT 1
                """, (aggregate_id, aggregate_type)).fetchone()

            if row:
                return Snapshot(
                    id=row["id"],
                    aggregate_id=row["aggregate_id"],
                    aggregate_type=row["aggregate_type"],
                    version=row["version"],
                    state=json.loads(row["state"]),
                    timestamp=row["timestamp"]
                )
        return None

    def should_snapshot(self, version: int) -> bool:
        """Check if aggregate should be snapshotted."""
        return version % self.SNAPSHOT_INTERVAL == 0

    # ─── Projections ───

    def get_projection_checkpoint(self, projection_name: str) -> int:
        """Get last processed version for projection."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT last_version FROM projection_checkpoints WHERE projection_name = ?",
                (projection_name,)
            ).fetchone()
            return row["last_version"] if row else 0

    def update_projection_checkpoint(self, projection_name: str, stream: str, version: int) -> None:
        """Update projection checkpoint."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO projection_checkpoints
                (projection_name, stream, last_version, updated_at)
                VALUES (?, ?, ?, ?)
            """, (projection_name, stream, version, datetime.utcnow().isoformat() + "Z"))
            conn.commit()

    # ─── Dead Letters ───

    def add_dead_letter(
        self,
        stream: str,
        version: int,
        event: Event,
        error: str
    ) -> None:
        """Store failed event for later inspection."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO dead_letters (stream, version, event_data, error, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (stream, version, event.to_json().decode(), error,
                  datetime.utcnow().isoformat() + "Z"))
            conn.commit()

    def get_dead_letters(self, limit: int = 100) -> list[dict]:
        """Get unprocessed dead letters."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM dead_letters WHERE attempts < 3
                ORDER BY created_at LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def retry_dead_letter(self, dead_letter_id: int) -> None:
        """Increment attempt count for dead letter."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE dead_letters SET attempts = attempts + 1, last_attempt = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat() + "Z", dead_letter_id))
            conn.commit()

    # ─── Helpers ───

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        return Event(
            event_type=row["event_type"],
            aggregate_id=row["aggregate_id"],
            aggregate_type=row["aggregate_type"],
            payload=json.loads(row["payload"]),
            event_id=row["event_id"],
            version=row["version"],
            timestamp=row["timestamp"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )

    # ─── Aggregate Reconstruction ───

    def reconstruct_aggregate(
        self,
        aggregate_id: str,
        aggregate_type: str,
        snapshot_interval: int = 100
    ) -> tuple[dict[str, Any], int]:
        """
        Reconstruct aggregate state from events + snapshot.

        Returns:
            (state_dict, version)
        """
        # Try to get snapshot
        snapshot = self.get_snapshot(aggregate_id, aggregate_type)
        if snapshot:
            state = snapshot.state.copy()
            from_version = snapshot.version
        else:
            state = {}
            from_version = 0

        # Apply events after snapshot
        events = self.read_aggregate(aggregate_id, aggregate_type, from_version)
        for event in events:
            # Apply event to state (override with event payload)
            state.update(event.payload)

        current_version = self.get_version(f"{aggregate_type}-{aggregate_id}")
        return state, current_version


# ─── Exceptions ───

class ConcurrencyError(Exception):
    """Optimistic concurrency conflict."""


# ─── Global Instance ───

_global_store: EventStore | None = None


def get_event_store(db_path: str | None = None) -> EventStore:
    """Get or create global event store instance."""
    global _global_store
    if _global_store is None:
        _global_store = EventStore(db_path)
    return _global_store


# ─── Repository Pattern Helper ───

class AggregateRepository:
    """Base repository for event-sourced aggregates."""

    def __init__(
        self,
        event_store: EventStore,
        aggregate_type: str,
        snapshot_interval: int = 100
    ):
        self.store = event_store
        self.aggregate_type = aggregate_type
        self.snapshot_interval = snapshot_interval

    def get_stream(self, aggregate_id: str) -> str:
        return f"{self.aggregate_type}-{aggregate_id}"

    def save(self, aggregate_id: str, events: list[Event], expected_version: int) -> int:
        """Save events for aggregate."""
        stream = self.get_stream(aggregate_id)
        new_version = self.store.append(stream, events, expected_version)

        # Check if snapshot needed
        if self.store.should_snapshot(events[-1].version):
            # Aggregate should implement get_state()
            pass  # Handled by aggregate

        return new_version

    def load(self, aggregate_id: str) -> tuple[dict[str, Any], int]:
        """Load aggregate state and version."""
        return self.store.reconstruct_aggregate(
            aggregate_id, self.aggregate_type
        )

"""
aig Multi-Region Replication
====================================
Cross-region data replication with conflict resolution.

Autor: aig Team
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from .config import REGIONS
except ImportError:
    from config import REGIONS


# ── Conflict Resolution Strategies ─────────────────────────────


class ConflictStrategy(Enum):
    LAST_WRITE_WINS = "last_write_wins"
    MERGE = "merge"
    MANUAL = "manual"


# ── Replication Record ─────────────────────────────────────────


@dataclass
class ReplicationRecord:
    """A single data record with metadata for replication."""

    key: str
    value: Any
    source_region: str
    timestamp: float = field(default_factory=time.time)
    version: int = 1
    conflict_strategy: ConflictStrategy = ConflictStrategy.LAST_WRITE_WINS

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "source_region": self.source_region,
            "timestamp": self.timestamp,
            "version": self.version,
            "conflict_strategy": self.conflict_strategy.value,
        }


# ── Redis Replication Config ───────────────────────────────────


REDIS_REPLICA_CONFIG: dict[str, dict[str, Any]] = {
    "eu-west": {
        "primary": {"host": "redis-eu-west", "port": 6379},
        "replicas": [
            {"host": "redis-eu-west-replica-1", "port": 6379},
            {"host": "redis-eu-west-replica-2", "port": 6379},
        ],
    },
    "us-east": {
        "primary": {"host": "redis-us-east", "port": 6379},
        "replicas": [
            {"host": "redis-us-east-replica-1", "port": 6379},
        ],
    },
    "ap-south": {
        "primary": {"host": "redis-ap-south", "port": 6379},
        "replicas": [
            {"host": "redis-ap-south-replica-1", "port": 6379},
        ],
    },
}


# ── SQLite WAL Setup ───────────────────────────────────────────


def _init_sqlite_wal(db_path: str) -> sqlite3.Connection:
    """Open SQLite with WAL mode for concurrent reads."""
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS replication_log (
            key TEXT PRIMARY KEY,
            value TEXT,
            source_region TEXT,
            timestamp REAL,
            version INTEGER DEFAULT 1
        )
        """
    )
    return conn


# ── Replication Manager ────────────────────────────────────────


class ReplicationManager:
    """Manages cross-region data replication."""

    def __init__(
        self,
        local_region: str,
        db_path: str = "replication.db",
        strategy: ConflictStrategy = ConflictStrategy.LAST_WRITE_WINS,
    ):
        self.local_region = local_region
        self.db_path = db_path
        self.strategy = strategy
        self.conn = _init_sqlite_wal(db_path)
        self._replication_log: list[ReplicationRecord] = []
        self._replication_stats: dict[str, int] = {
            "synced": 0,
            "conflicts": 0,
            "failed": 0,
        }

    # ── Core Operations ────────────────────────────────────────

    def write(self, key: str, value: Any) -> ReplicationRecord:
        """Write a record locally and queue for replication."""
        record = ReplicationRecord(
            key=key,
            value=json.dumps(value) if not isinstance(value, str) else value,
            source_region=self.local_region,
            timestamp=time.time(),
            version=self._next_version(key),
            conflict_strategy=self.strategy,
        )
        self._persist_record(record)
        self._replication_log.append(record)
        return record

    def read(self, key: str) -> ReplicationRecord | None:
        """Read a record from the local store."""
        cur = self.conn.execute(
            "SELECT key, value, source_region, timestamp, version FROM replication_log WHERE key = ?",
            (key,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return ReplicationRecord(
            key=row[0],
            value=row[1],
            source_region=row[2],
            timestamp=row[3],
            version=row[4],
        )

    def sync_data(
        self,
        source_region: str,
        target_region: str,
        data_type: str = "all",
    ) -> dict[str, Any]:
        """Sync data between two regions and return summary."""
        if source_region not in REGIONS or target_region not in REGIONS:
            return {"status": "error", "message": "Invalid region"}

        source_records = self._get_region_records(source_region)
        synced = 0
        conflicts = 0

        for record in source_records:
            existing = self.read(record.key)
            if existing is None:
                self._persist_record(record)
                synced += 1
            elif existing.source_region == target_region:
                continue
            else:
                resolution = self._resolve_conflict(existing, record)
                if resolution:
                    self._persist_record(resolution)
                    synced += 1
                else:
                    conflicts += 1

        self._replication_stats["synced"] += synced
        self._replication_stats["conflicts"] += conflicts

        return {
            "status": "ok",
            "source": source_region,
            "target": target_region,
            "data_type": data_type,
            "synced": synced,
            "conflicts": conflicts,
        }

    # ── Conflict Resolution ────────────────────────────────────

    def _resolve_conflict(
        self, existing: ReplicationRecord, incoming: ReplicationRecord
    ) -> ReplicationRecord | None:
        """Resolve a conflict between two records."""
        if incoming.timestamp > existing.timestamp:
            return incoming
        if incoming.timestamp < existing.timestamp:
            return None
        if incoming.version > existing.version:
            return incoming
        return None

    # ── Internals ──────────────────────────────────────────────

    def _next_version(self, key: str) -> int:
        cur = self.conn.execute(
            "SELECT version FROM replication_log WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        return (row[0] + 1) if row else 1

    def _persist_record(self, record: ReplicationRecord) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO replication_log (key, value, source_region, timestamp, version)
            VALUES (?, ?, ?, ?, ?)
            """,
            (record.key, record.value, record.source_region, record.timestamp, record.version),
        )
        self.conn.commit()

    def _get_region_records(self, region: str) -> list[ReplicationRecord]:
        cur = self.conn.execute(
            "SELECT key, value, source_region, timestamp, version FROM replication_log WHERE source_region = ?",
            (region,),
        )
        return [
            ReplicationRecord(
                key=r[0], value=r[1], source_region=r[2], timestamp=r[3], version=r[4]
            )
            for r in cur.fetchall()
        ]

    def get_stats(self) -> dict[str, int]:
        return dict(self._replication_stats)

    def close(self) -> None:
        self.conn.close()

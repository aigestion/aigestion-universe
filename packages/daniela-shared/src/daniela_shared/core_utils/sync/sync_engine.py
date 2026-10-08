"""
Background Sync Engine for aig.

Reliable offline-first sync with exponential backoff,
conflict resolution, and tombstone support.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.sync.crdt import ConflictResolver, get_conflict_resolver


class SyncStatus(Enum):
    """Sync operation status."""
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


@dataclass
class SyncOperation:
    """A single sync operation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    type: str = "CREATE"  # CREATE, UPDATE, DELETE
    collection: str = ""
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    status: SyncStatus = SyncStatus.PENDING
    error: str | None = None


@dataclass
class SyncCheckpoint:
    """Checkpoint for incremental sync."""
    collection: str
    last_sync: datetime
    last_id: str | None = None


class SyncEngine:
    """Reliable background sync with exponential backoff."""

    def __init__(
        self,
        local_db: Any,
        remote_api: Any,
        conflict_resolver: ConflictResolver | None = None,
        max_retries: int = 5,
        base_delay: float = 1.0,
        batch_size: int = 100,
    ):
        self.local_db = local_db
        self.remote_api = remote_api
        self.conflict_resolver = conflict_resolver or get_conflict_resolver()
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.batch_size = batch_size

        self._queue: asyncio.Queue[SyncOperation] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task | None = None
        self._checkpoints: dict[str, SyncCheckpoint] = {}

    async def start(self) -> None:
        """Start background sync loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())

    async def stop(self) -> None:
        """Stop background sync."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def queue(self, operation: SyncOperation) -> None:
        """Queue a sync operation."""
        await self._queue.put(operation)

    async def queue_many(self, operations: list[SyncOperation]) -> None:
        """Queue multiple sync operations."""
        for op in operations:
            await self._queue.put(op)

    async def sync_now(self) -> None:
        """Force immediate sync of all pending operations."""
        pending = await self.local_db.get_pending_operations()
        for op in pending:
            await self.queue(op)
        # Wait for queue to drain
        await self._queue.join()

    async def _sync_loop(self) -> None:
        """Main sync loop."""
        while self._running:
            try:
                operation = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,
                )
                await self._process_operation(operation)
                self._queue.task_done()
            except TimeoutError:
                continue
            except Exception as e:
                print(f"[SyncEngine] Error: {e}")
                await asyncio.sleep(self.base_delay)

    async def _process_operation(self, operation: SyncOperation) -> None:
        """Process a single sync operation."""
        operation.status = SyncStatus.SYNCING

        try:
            # Push to remote
            result = await self.remote_api.push(
                collection=operation.collection,
                data=operation.data,
                operation_type=operation.type,
            )

            # Check for conflicts
            if result.get("conflict"):
                resolved = self.conflict_resolver.resolve(
                    local=operation.data,
                    remote=result["remote"],
                )
                await self.remote_api.push(
                    collection=operation.collection,
                    data=resolved,
                    operation_type="UPDATE",
                )
                operation.status = SyncStatus.CONFLICT
            else:
                operation.status = SyncStatus.SYNCED

            # Update local DB
            await self.local_db.update_sync_status(
                operation.id,
                operation.status,
            )

        except Exception as e:
            operation.retry_count += 1
            operation.error = str(e)

            if operation.retry_count >= self.max_retries:
                operation.status = SyncStatus.FAILED
                await self.local_db.update_sync_status(
                    operation.id,
                    operation.status,
                    error=str(e),
                )
            else:
                # Exponential backoff
                delay = self.base_delay * (2 ** operation.retry_count)
                await asyncio.sleep(delay)
                await self._queue.put(operation)

    async def pull(self, collection: str, since: datetime | None = None) -> int:
        """Pull changes from remote. Returns count of changes applied."""
        checkpoint = self._checkpoints.get(collection)
        last_sync = since or (checkpoint.last_sync if checkpoint else None)

        changes = await self.remote_api.pull(collection, last_sync)
        applied = 0

        for change in changes:
            # Check for local conflicts
            local = await self.local_db.get(change["id"])
            if local and local.get("modified", datetime.min) > change.get("modified", datetime.min):
                # Conflict - resolve with CRDT
                resolved = self.conflict_resolver.resolve(local, change)
                await self.local_db.upsert(resolved)
            else:
                await self.local_db.upsert(change)
            applied += 1

        # Update checkpoint
        self._checkpoints[collection] = SyncCheckpoint(
            collection=collection,
            last_sync=datetime.utcnow(),
            last_id=changes[-1]["id"] if changes else None,
        )

        return applied

    async def get_stats(self) -> dict[str, Any]:
        """Get sync statistics."""
        pending = await self.local_db.count_by_status(SyncStatus.PENDING)
        syncing = await self.local_db.count_by_status(SyncStatus.SYNCING)
        synced = await self.local_db.count_by_status(SyncStatus.SYNCED)
        failed = await self.local_db.count_by_status(SyncStatus.FAILED)
        conflict = await self.local_db.count_by_status(SyncStatus.CONFLICT)

        return {
            "pending": pending,
            "syncing": syncing,
            "synced": synced,
            "failed": failed,
            "conflict": conflict,
            "total": pending + syncing + synced + failed + conflict,
            "running": self._running,
            "queue_size": self._queue.qsize(),
        }


class OfflineFirstRepository:
    """Repository pattern for offline-first data access."""

    def __init__(
        self,
        local_db: Any,
        remote_api: Any,
        sync_engine: SyncEngine,
        collection: str,
    ):
        self.local_db = local_db
        self.remote_api = remote_api
        self.sync_engine = sync_engine
        self.collection = collection

    async def get(self, id: str) -> dict | None:
        """Get by ID (local first)."""
        return await self.local_db.get(id)

    async def get_all(self, filters: dict | None = None) -> list[dict]:
        """Get all (local first)."""
        return await self.local_db.get_all(self.collection, filters)

    async def create(self, data: dict) -> dict:
        """Create (local first, queue for sync)."""
        doc = {
            "id": str(uuid.uuid4())[:12],
            **data,
            "created": datetime.utcnow().isoformat(),
            "modified": datetime.utcnow().isoformat(),
            "sync_status": SyncStatus.PENDING.value,
        }

        # Save locally
        await self.local_db.upsert(doc)

        # Queue for sync
        await self.sync_engine.queue(SyncOperation(
            type="CREATE",
            collection=self.collection,
            data=doc,
        ))

        return doc

    async def update(self, id: str, data: dict) -> dict | None:
        """Update (local first, queue for sync)."""
        existing = await self.local_db.get(id)
        if not existing:
            return None

        updated = {
            **existing,
            **data,
            "modified": datetime.utcnow().isoformat(),
            "sync_status": SyncStatus.PENDING.value,
        }

        # Save locally
        await self.local_db.upsert(updated)

        # Queue for sync
        await self.sync_engine.queue(SyncOperation(
            type="UPDATE",
            collection=self.collection,
            data=updated,
        ))

        return updated

    async def delete(self, id: str) -> bool:
        """Delete (tombstone, queue for sync)."""
        existing = await self.local_db.get(id)
        if not existing:
            return False

        # Tombstone
        tombstone = {
            **existing,
            "deleted": True,
            "modified": datetime.utcnow().isoformat(),
            "sync_status": SyncStatus.PENDING.value,
        }

        await self.local_db.upsert(tombstone)

        # Queue for sync
        await self.sync_engine.queue(SyncOperation(
            type="DELETE",
            collection=self.collection,
            data=tombstone,
        ))

        return True

    async def sync(self) -> dict:
        """Force sync and return stats."""
        await self.sync_engine.sync_now()
        return await self.sync_engine.get_stats()


# ─── Global Instance ───

_global_sync_engine: SyncEngine | None = None


def get_sync_engine(
    local_db: Any = None,
    remote_api: Any = None,
) -> SyncEngine:
    """Get or create global sync engine."""
    global _global_sync_engine
    if _global_sync_engine is None:
        if local_db is None or remote_api is None:
            raise ValueError("local_db and remote_api required for first initialization")
        _global_sync_engine = SyncEngine(local_db, remote_api)
    return _global_sync_engine

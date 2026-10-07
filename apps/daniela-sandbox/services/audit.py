"""Append-only, hash-chained audit log for sandbox executions.

Each entry is chained to the previous via SHA-256, so tampering
with any historical entry breaks the chain (detectable via verify()).
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AuditEntry:
    seq: int
    timestamp: float
    backend: str
    command: str
    exit_code: Optional[int]
    duration_ms: float
    digest: str = ""


class AuditLog:
    """Ring-buffer audit log with hash chaining."""

    def __init__(self, capacity: int = 1000) -> None:
        self.capacity = capacity
        self._entries: List[AuditEntry] = []
        self._chain = hashlib.sha256(b"daniela-sandbox-genesis").hexdigest()
        self._seq = 0

    def record(
        self,
        backend: str,
        command: str,
        *,
        exit_code: Optional[int],
        duration_ms: float,
    ) -> AuditEntry:
        self._seq += 1
        payload = json.dumps(
            {
                "seq": self._seq,
                "backend": backend,
                "command": command,
                "exit_code": exit_code,
                "duration_ms": round(duration_ms, 3),
            },
            sort_keys=True,
        )
        self._chain = hashlib.sha256(
            (self._chain + payload).encode()
        ).hexdigest()

        entry = AuditEntry(
            seq=self._seq,
            timestamp=time.time(),
            backend=backend,
            command=command,
            exit_code=exit_code,
            duration_ms=duration_ms,
            digest=self._chain,
        )
        self._entries.append(entry)
        if len(self._entries) > self.capacity:
            self._entries.pop(0)
        return entry

    def entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [
            {
                "seq": e.seq,
                "timestamp": e.timestamp,
                "backend": e.backend,
                "command": e.command,
                "exit_code": e.exit_code,
                "duration_ms": round(e.duration_ms, 3),
                "digest": e.digest,
            }
            for e in self._entries[-limit:]
        ]

    def verify(self) -> bool:
        """Recompute the chain; True if intact."""
        chain = hashlib.sha256(b"daniela-sandbox-genesis").hexdigest()
        for e in self._entries:
            payload = json.dumps(
                {
                    "seq": e.seq,
                    "backend": e.backend,
                    "command": e.command,
                    "exit_code": e.exit_code,
                    "duration_ms": round(e.duration_ms, 3),
                },
                sort_keys=True,
            )
            chain = hashlib.sha256((chain + payload).encode()).hexdigest()
        return chain == self._chain

    def latest_digest(self) -> str:
        return self._chain

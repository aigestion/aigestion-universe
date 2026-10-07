"""Two-way sync between Daniela memory and an Obsidian vault."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
import time

from .converter import MemoryDoc, markdown_to_memory, memory_to_markdown


class SyncDirection(str, Enum):
    VAULT_TO_MEMORY = "vault_to_memory"
    MEMORY_TO_VAULT = "memory_to_vault"
    BIDIRECTIONAL = "bidirectional"


class VaultSync:
    """Sync Daniela memories <-> an Obsidian vault folder."""

    def __init__(self, vault_path: str | Path, *, direction: SyncDirection = SyncDirection.BIDIRECTIONAL) -> None:
        self.vault_path = Path(vault_path)
        self.direction = direction
        self._last_sync: Dict[str, float] = {}

    async def sync(self, memories: List[MemoryDoc]) -> Dict[str, int]:
        """Sync a batch of memories into the vault."""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        written = 0
        for mem in memories:
            note_path = self.vault_path / f"{mem.id}.md"
            if not note_path.exists() or self._changed(mem, note_path):
                note_path.write_text(
                    memory_to_markdown(mem), encoding="utf-8"
                )
                self._last_sync[mem.id] = time.time()
                written += 1
        return {"written": written, "total": len(memories)}

    def scan_vault(self) -> List[MemoryDoc]:
        """Read all notes in the vault back into MemoryDocs."""
        docs: List[MemoryDoc] = []
        if not self.vault_path.exists():
            return docs
        for note in sorted(self.vault_path.glob("*.md")):
            try:
                docs.append(markdown_to_memory(note.read_text(encoding="utf-8")))
            except Exception:
                continue
        return docs

    def _changed(self, mem: MemoryDoc, note_path: Path) -> bool:
        last = self._last_sync.get(mem.id, 0)
        try:
            return note_path.stat().st_mtime > last
        except OSError:
            return True

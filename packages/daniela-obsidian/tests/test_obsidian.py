"""Tests for Obsidian vault sync (converter + VaultSync)."""
import asyncio
import sys
from datetime import datetime

sys.path.insert(0, r"C:\Users\Alejandro\aigestion-universe\packages\daniela-obsidian")

from daniela_obsidian import (
    MemoryDoc,
    VaultSync,
    markdown_to_memory,
    memory_to_markdown,
)


def test_roundtrip():
    mem = MemoryDoc(
        id="abc123",
        tier="semantic",
        content="Daniela runs on port 9200",
        importance=0.9,
        tags=["daniela", "core"],
        created_at=datetime(2026, 1, 1, 12, 0),
    )
    md = memory_to_markdown(mem)
    assert "---" in md
    assert "Daniela runs on port 9200" in md

    back = markdown_to_memory(md)
    assert back.id == "abc123"
    assert back.tier == "semantic"
    assert back.content == "Daniela runs on port 9200"
    assert abs(back.importance - 0.9) < 1e-6
    assert "daniela" in back.tags


def test_markdown_without_frontmatter():
    back = markdown_to_memory("just some text")
    assert back.content == "just some text"
    assert back.tier == "episodic"  # default


def test_vault_sync(tmp_path):
    sync = VaultSync(tmp_path / "vault")
    memories = [
        MemoryDoc(id="m1", tier="episodic", content="hello", tags=["test"]),
        MemoryDoc(id="m2", tier="semantic", content="world", tags=["test"]),
    ]
    report = asyncio.run(sync.sync(memories))
    assert report == {"written": 2, "total": 2}

    # Second sync writes nothing (unchanged)
    report = asyncio.run(sync.sync(memories))
    assert report["written"] == 0

    # Scan reads them back
    docs = sync.scan_vault()
    assert len(docs) == 2
    assert {d.id for d in docs} == {"m1", "m2"}


def test_scan_empty_vault(tmp_path):
    sync = VaultSync(tmp_path / "missing")
    assert sync.scan_vault() == []

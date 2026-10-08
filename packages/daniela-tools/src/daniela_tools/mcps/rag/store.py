"""SQLite persistence for documents and chunks.

Backed by the ``daniela_memory.db`` that already existed in the project. The
original schema had a single ``knowledge_base`` table, which is preserved and
still written to, so external readers of that table keep working. Chunks live
in a table added by this module.

Everything degrades to an in-memory database when the file cannot be opened, so
retrieval never fails just because storage is unavailable.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from collections.abc import Iterable
from datetime import UTC, datetime

__all__ = ["DocumentStore", "DEFAULT_DB_PATH"]

DEFAULT_DB_PATH = "/root/apps/aig/phone/core/daniela_memory.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rag_documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    source TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    source TEXT DEFAULT '',
    content TEXT NOT NULL,
    indexed_text TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES rag_documents(doc_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc ON rag_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);
"""


class DocumentStore:
    """SQLite-backed document and chunk storage."""

    def __init__(self, path: str | None = None):
        self.path = path if path is not None else DEFAULT_DB_PATH
        self._lock = threading.RLock()
        self._in_memory = False
        self._conn = self._connect()
        self._migrate()

    # -- connection ------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        if self.path == ":memory:":
            self._in_memory = True
            return sqlite3.connect(":memory:", check_same_thread=False)
        try:
            directory = os.path.dirname(self.path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            return sqlite3.connect(self.path, check_same_thread=False)
        except Exception:
            # Read-only filesystem or a locked file: keep going in memory.
            self._in_memory = True
            self.path = ":memory:"
            return sqlite3.connect(":memory:", check_same_thread=False)

    def _migrate(self) -> None:
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    @property
    def persistent(self) -> bool:
        """False when backed by memory instead of a file."""
        return not self._in_memory

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    # -- writes ----------------------------------------------------------
    def upsert_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        category: str = "general",
        source: str = "",
    ) -> None:
        """Insert or replace a document, mirroring it into ``knowledge_base``."""
        now = self._now()
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO rag_documents"
                " (doc_id, title, content, category, source, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (doc_id, title, content, category, source, now),
            )
            self._conn.execute(
                "INSERT OR REPLACE INTO knowledge_base (title, content, category, updated_at)"
                " VALUES (?, ?, ?, ?)",
                (title, content, category, now),
            )
            self._conn.commit()

    def replace_chunks(self, doc_id: str, chunks: Iterable[dict[str, object]]) -> int:
        """Replace all chunks belonging to ``doc_id``. Returns the chunk count."""
        now = self._now()
        rows = [
            (
                str(chunk["id"]),
                doc_id,
                int(chunk.get("ordinal", 0)),
                str(chunk.get("title", "")),
                str(chunk.get("category", "general")),
                str(chunk.get("source", "")),
                str(chunk.get("content", "")),
                str(chunk.get("indexed_text", chunk.get("content", ""))),
                now,
            )
            for chunk in chunks
        ]
        with self._lock:
            self._conn.execute("DELETE FROM rag_chunks WHERE doc_id = ?", (doc_id,))
            self._conn.executemany(
                "INSERT OR REPLACE INTO rag_chunks"
                " (chunk_id, doc_id, ordinal, title, category, source, content, indexed_text, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            self._conn.commit()
        return len(rows)

    def delete_document(self, doc_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM rag_chunks WHERE doc_id = ?", (doc_id,))
            self._conn.execute("DELETE FROM rag_documents WHERE doc_id = ?", (doc_id,))
            self._conn.commit()

    # -- reads -----------------------------------------------------------
    def load_chunks(self, category: str | None = None) -> list[dict]:
        """All stored chunks, optionally restricted to one category."""
        query = (
            "SELECT chunk_id, doc_id, ordinal, title, category, source, content, indexed_text"
            " FROM rag_chunks"
        )
        params: tuple = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        query += " ORDER BY doc_id, ordinal"
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [
            {
                "id": row[0],
                "doc_id": row[1],
                "ordinal": row[2],
                "title": row[3],
                "category": row[4],
                "source": row[5],
                "content": row[6],
                "indexed_text": row[7],
            }
            for row in rows
        ]

    def load_documents(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT doc_id, title, content, category, source, updated_at"
                " FROM rag_documents ORDER BY doc_id"
            ).fetchall()
        return [
            {
                "doc_id": r[0],
                "title": r[1],
                "content": r[2],
                "category": r[3],
                "source": r[4],
                "updated_at": r[5],
            }
            for r in rows
        ]

    def stats(self) -> dict:
        """Row counts, used by the dashboard and by tests."""
        with self._lock:
            docs = self._conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0]
            chunks = self._conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
            kb = self._conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0]
        return {
            "documents": docs,
            "chunks": chunks,
            "knowledge_base": kb,
            "path": self.path,
            "persistent": self.persistent,
        }

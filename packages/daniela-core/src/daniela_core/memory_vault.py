"""Memory Vault — persistent long-term memory with knowledge graph.

Canonical promotion of the legacy ``agents_memory/memory_vault.py`` into the
``daniela_core`` package (Memory Vault v2, idea #4):

- Long-term persistence in SQLite (stdlib, zero dependencies).
- :meth:`MemoryVault.record` stores + auto-links by significant tokens (graph).
- :meth:`MemoryVault.recall` retrieves by overlap + 1-hop graph expansion.
- No FTS5 in this sqlite: TF scoring in Python (honest and sufficient
  at this scale; migrate to FTS5/vectors when it grows — see
  :mod:`daniela_core.memory_semantic`).

Database location (in order):
  1. ``MEMORY_RAG_DB`` environment variable (tests, custom deployments).
  2. ``packages/daniela-core/data/memory_rag.db`` (package default).

The production database is git-ignored: local memory, never versioned.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = _PACKAGE_DIR / "data" / "memory_rag.db"


def resolve_db_path() -> Path:
    """Database path: ``MEMORY_RAG_DB`` wins, else the package default."""
    override = os.environ.get("MEMORY_RAG_DB")
    return Path(override) if override else DEFAULT_DB_PATH


STOPWORDS = frozenset(
    "de la el en y los del se las una por con para como esta este son fue han "  # noqa: SIM905 - word list reads better as string
    "sus entre pero sus mas muy sin sobre tambien hasta desde donde cuando "
    "porque pues tan hay este esta estos estas ese esa esos esas aquel aquello "
    "que los las les nos os me te se mi tu su nuestro vuestro este aquel "
    "the and for are with this that from have has had were was are been "
    "que del los una unos unas al lo le les".split()
)

TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]{4,}")

#: Minimum shared significant tokens to auto-link two memories.
MIN_SHARED_TOKENS = 2


def tokens_significativos(texto: str | None) -> set[str]:
    """Lowercase tokens >= 4 chars without ES/EN stopwords."""
    return {t for t in TOKEN_RE.findall((texto or "").lower()) if t not in STOPWORDS}


class MemoryVault:
    """Long-term memory vault with knowledge graph."""

    def __init__(self, db_path: Path | str | None = None):
        if db_path is None:
            self.db_path = resolve_db_path()
        else:
            self.db_path = Path(db_path)

    def _con(self) -> sqlite3.Connection:
        if str(self.db_path) != ":memory:":
            parent = self.db_path.parent
            if str(parent):
                parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(self.db_path))
        con.execute(
            """CREATE TABLE IF NOT EXISTS rag_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT, content TEXT, timestamp TEXT)"""
        )
        con.execute(
            """CREATE TABLE IF NOT EXISTS memory_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_a INTEGER, doc_b INTEGER, relacion TEXT,
                peso REAL, timestamp TEXT)"""
        )
        return con

    # ── Escritura ────────────────────────────────────────────────

    def record(
        self,
        source: str,
        content: str,
        enlaces: list[tuple[int, str]] | None = None,
        auto_link: bool = True,
    ) -> int:
        """Store a memory; returns its id. Auto-links with recent docs
        sharing >= 2 tokens (max 5)."""
        if not (content or "").strip():
            raise ValueError("content vacio")  # noqa: TRY003 - CLI-style short error
        ahora = datetime.now().isoformat()
        con = self._con()
        try:
            cur = con.execute(
                "INSERT INTO rag_docs (source, content, timestamp) VALUES (?, ?, ?)",
                (source, content, ahora),
            )
            doc_id = cur.lastrowid or 0
            if enlaces:
                for otro, relacion in enlaces:
                    con.execute(
                        "INSERT INTO memory_links (doc_a, doc_b, relacion, peso, timestamp)"
                        " VALUES (?, ?, ?, ?, ?)",
                        (doc_id, otro, relacion, 1.0, ahora),
                    )
            if auto_link:
                self._auto_enlazar(con, doc_id, content, ahora)
            con.commit()
            return doc_id
        finally:
            con.close()

    def _auto_enlazar(self, con: sqlite3.Connection, doc_id: int, content: str, ahora: str) -> int:
        toks = tokens_significativos(content)
        if len(toks) < MIN_SHARED_TOKENS:
            return 0
        recientes = con.execute(
            "SELECT id, content FROM rag_docs WHERE id != ? ORDER BY id DESC LIMIT 200",
            (doc_id,),
        ).fetchall()
        candidatos = []
        for otro_id, otro_txt in recientes:
            shared = toks & tokens_significativos(otro_txt or "")
            if len(shared) >= MIN_SHARED_TOKENS:
                candidatos.append((len(shared), otro_id))
        creados = 0
        for peso, otro_id in sorted(candidatos, reverse=True)[:5]:
            con.execute(
                "INSERT INTO memory_links (doc_a, doc_b, relacion, peso, timestamp)"
                " VALUES (?, ?, ?, ?, ?)",
                (doc_id, otro_id, "auto:tokens", float(peso), ahora),
            )
            creados += 1
        return creados

    # ── Lectura ──────────────────────────────────────────────────

    def recall(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Recall by token overlap + 1-hop graph expansion."""
        qtoks = tokens_significativos(query)
        if not qtoks:
            return []
        con = self._con()
        try:
            docs = con.execute("SELECT id, source, content, timestamp FROM rag_docs").fetchall()
            links = con.execute("SELECT doc_a, doc_b, relacion, peso FROM memory_links").fetchall()
        finally:
            con.close()

        scored = []
        for doc_id, source, content, ts in docs:
            overlap = qtoks & tokens_significativos(content or "")
            if overlap:
                scored.append(
                    {
                        "id": doc_id,
                        "source": source,
                        "content": (content or "")[:600],
                        "timestamp": ts,
                        "score": round(len(overlap) / max(1, len(qtoks)), 3),
                        "via": "directo",
                        "tokens": sorted(overlap),
                    }
                )
        scored.sort(key=lambda d: d["score"], reverse=True)
        top = scored[: max(1, top_k)]
        top = self._expand_graph(top, links, por_id={d["id"]: d for d in scored})
        top.sort(key=lambda d: (d["via"] == "directo", d["score"]), reverse=True)
        return top[:top_k]

    def _expand_graph(
        self,
        top: list[dict[str, Any]],
        links: list[tuple],
        por_id: dict[int, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """1-hop expansion: neighbours of the top 2, even without overlap."""
        vecinas: dict[int, float] = {}
        protagonistas = {d["id"] for d in top[:2]}
        for a, b, _relacion, peso in links:
            if a in protagonistas and b not in protagonistas:
                vecinas[b] = max(vecinas.get(b, 0.0), 0.5 * float(peso or 1))
            elif b in protagonistas and a not in protagonistas:
                vecinas[a] = max(vecinas.get(a, 0.0), 0.5 * float(peso or 1))
        if not vecinas:
            return top
        con = self._con()
        try:
            # Placeholders only (? * n) — no user input in the SQL string.
            ids = ",".join("?" * len(vecinas))
            filas = con.execute(
                f"SELECT id, source, content, timestamp FROM rag_docs WHERE id IN ({ids})",  # noqa: S608 - placeholders only
                tuple(vecinas),
            ).fetchall()
        finally:
            con.close()
        vistos = {d["id"] for d in top}
        for doc_id, source, content, ts in filas:
            if doc_id in vistos or doc_id in protagonistas:
                continue
            base = por_id.get(doc_id)
            if base is not None:
                copia = dict(base)
                copia["via"] = "grafo"
            else:
                copia = {
                    "id": doc_id,
                    "source": source,
                    "content": (content or "")[:600],
                    "timestamp": ts,
                    "via": "grafo",
                    "tokens": [],
                }
            copia["score"] = round(min(0.49, 0.1 + 0.05 * vecinas[doc_id]), 3)
            top.append(copia)
        return top

    def recientes(self, limite: int = 20) -> list[dict[str, Any]]:
        """Latest memories, no query."""
        try:
            limite = int(limite)
        except (TypeError, ValueError):
            limite = 20
        limite = max(1, min(limite, 200))
        con = self._con()
        try:
            filas = con.execute(
                "SELECT id, source, content, timestamp FROM rag_docs ORDER BY id DESC LIMIT ?",
                (limite,),
            ).fetchall()
        finally:
            con.close()
        return [
            {
                "id": i,
                "source": s,
                "content": (c or "")[:600],
                "timestamp": t,
                "via": "reciente",
                "score": None,
                "tokens": [],
            }
            for i, s, c, t in filas
        ]

    def olvidar(self, doc_id: int) -> dict[str, int]:
        """Delete a memory and ALL its links (both directions)."""
        try:
            doc_id = int(doc_id)
        except (TypeError, ValueError):
            return {"docs": 0, "enlaces": 0}
        con = self._con()
        try:
            enlaces = con.execute(
                "DELETE FROM memory_links WHERE doc_a = ? OR doc_b = ?",
                (doc_id, doc_id),
            ).rowcount
            docs = con.execute("DELETE FROM rag_docs WHERE id = ?", (doc_id,)).rowcount
            con.commit()
        finally:
            con.close()
        return {"docs": int(docs or 0), "enlaces": int(enlaces or 0)}

    def stats(self) -> dict[str, Any]:
        """Counts + sources + latest memory."""
        con = self._con()
        try:
            docs = con.execute("SELECT COUNT(*) FROM rag_docs").fetchone()[0]
            links = con.execute("SELECT COUNT(*) FROM memory_links").fetchone()[0]
            fuentes = dict(
                con.execute("SELECT source, COUNT(*) FROM rag_docs GROUP BY source").fetchall()
            )
            ultimo = con.execute(
                "SELECT id, source, timestamp FROM rag_docs ORDER BY id DESC LIMIT 1"
            ).fetchone()
        finally:
            con.close()
        return {
            "db": str(self.db_path),
            "docs": docs,
            "links": links,
            "fuentes": fuentes,
            "ultimo": {"id": ultimo[0], "source": ultimo[1], "ts": ultimo[2]} if ultimo else None,
        }


# ── CLI ──────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Memory Vault (canonical)")
    sub = parser.add_subparsers(dest="cmd")

    p_rec = sub.add_parser("record", help="Guardar recuerdo")
    p_rec.add_argument("--source", required=True)
    p_rec.add_argument("--content", required=True)

    p_get = sub.add_parser("recall", help="Recuperar recuerdos")
    p_get.add_argument("query")
    p_get.add_argument("--top", type=int, default=5)

    p_recientes = sub.add_parser("recientes", help="Ultimos recuerdos")
    p_recientes.add_argument("--top", type=int, default=20)

    p_olvida = sub.add_parser("olvidar", help="Borra un recuerdo por id")
    p_olvida.add_argument("id", type=int)

    p_st = sub.add_parser("stats", help="Estadisticas")
    p_st.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    vault = MemoryVault()

    if args.cmd == "record":
        doc_id = vault.record(args.source, args.content)
        print(f"guardado id={doc_id}")  # noqa: T201 - CLI output
    elif args.cmd == "recall":
        for r in vault.recall(args.query, top_k=args.top):
            print(  # noqa: T201 - CLI output
                f"[{r['score']:.2f} {r['via']:8}] #{r['id']} ({r['source']}): "
                f"{r['content'][:100]}..."
            )
    elif args.cmd == "recientes":
        for r in vault.recientes(limite=args.top):
            print(f"#{r['id']} ({r['source']}): {r['content'][:100]}...")  # noqa: T201 - CLI output
    elif args.cmd == "olvidar":
        b = vault.olvidar(args.id)
        print(f"borrados: {b['docs']} doc(s), {b['enlaces']} enlace(s)")  # noqa: T201 - CLI output
    elif args.cmd == "stats":
        s = vault.stats()
        print(  # noqa: T201 - CLI output
            json.dumps(s, indent=2, ensure_ascii=False)
            if args.json
            else f"docs={s['docs']} links={s['links']} fuentes={s['fuentes']}"
        )
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

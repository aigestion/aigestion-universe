"""Memory Semantic — vector search over the MemoryVault.

Adds the vector layer **without touching MemoryVault**: reads the same
``rag_docs`` table and keeps vectors in a separate ``sqlite-vec`` virtual
table. If this module fails or sqlite-vec is not installed, the vault keeps
working exactly the same.

Why ``sqlite-vec`` and not Pinecone/Chroma
------------------------------------------
- It is a SQLite extension: **zero services**, zero quota, zero net latency.
- Works the same on PC and phone. An external service is not a real option
  on Termux/Pixel.
- ``memory_rag.db`` already exists and is SQLite: no data migration.

Embedding providers (swappable via env)
---------------------------------------
1. ``MEMORY_EMBED_PROVIDER=hashing`` (default, **what runs today**).
   Bag-of-words with feature hashing (MD5 -> bucket). No model, no net,
   no dependencies, deterministic. Captures **lexical** similarity well.
   Honest limitation: NO synonyms ("coche" won't match "automovil").

2. ``MEMORY_EMBED_PROVIDER=ollama`` -> real model via local Ollama
   (``MEMORY_EMBED_MODEL``, default ``nomic-embed-text``). Real semantics.
   Requires Ollama up with the model downloaded. Falls back to hashing.

3. ``MEMORY_EMBED_PROVIDER=gemini`` -> Gemini API. Requires a valid
   ``GEMINI_API_KEY``. Falls back to hashing.

Switching providers **invalidates stored vectors** (other dimension, other
space). That is why :meth:`MemorySemantic.reindex` exists and is cheap.

Usage:
    sem = MemorySemantic()  # uses MEMORY_RAG_DB or the package default
    sem.index_all()
    sem.search("proveedor Garcia", 5)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import logging
import math
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from daniela_core.memory_vault import MemoryVault, resolve_db_path

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

# Repo root: this module lives 4 levels deep
# (daniela_core/memory_semantic.py -> daniela_core -> src -> daniela-core -> packages -> root).
_REPO_ROOT = Path(__file__).resolve().parents[4]

DIM_HASHING = 256
PROVEEDOR_DEFECTO = "hashing"
MIN_DOC_CHARS = 40


# ── Embedding providers ────────────────────────────────────


def _l2_a_coseno(distancia_l2: float) -> float:
    """Convert the distance returned by sqlite-vec to cosine similarity.

    ``vec0`` returns **L2 (euclidean) distance**, not cosine. For vectors
    **normalized to norm 1** (as generated here) the exact identity holds::

        L2^2 = 2 - 2*cos   =>   cos = 1 - L2^2/2
    """
    c = 1.0 - (float(distancia_l2) ** 2) / 2.0
    return max(0.0, min(1.0, c))


def _embed_hashing(texto: str, dim: int = DIM_HASHING) -> list[float]:
    """Bag-of-words with feature hashing. No net, no model, deterministic.

    Each token falls in a bucket by MD5. Normalized to norm 1 so cosine is
    comparable across texts of different length.
    """
    vec = [0.0] * dim
    for token in (texto or "").lower().split():
        cubo = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim  # noqa: S324 - non-cryptographic feature hashing
        vec[cubo] += 1.0
    norma = math.sqrt(sum(x * x for x in vec))
    if norma == 0.0:
        return vec
    return [x / norma for x in vec]


def _url_util(nombre: str, defecto: str) -> str:
    """Read a URL from env, ignoring templates and invalid values.

    Real trap: a repo `.env` may carry `OLLAMA_URL=YOUR_VALUE_HERE`. Plain
    `os.getenv` returns the template (the key EXISTS) and urllib blows up.
    Discard explicitly.
    """
    valor = (os.getenv(nombre) or "").strip()
    if not valor or valor == "YOUR_VALUE_HERE" or not valor.startswith(("http://", "https://")):
        if valor:
            logger.info("%s=%r is not a valid URL (template?); using %s", nombre, valor, defecto)
        return defecto
    return valor.rstrip("/")


def _embed_ollama(texto: str, modelo: str) -> list[float] | None:
    """Real embedding via local Ollama. None when unavailable."""
    url = _url_util("OLLAMA_URL", "http://localhost:11434") + "/api/embeddings"
    cuerpo = json.dumps({"model": modelo, "prompt": texto}).encode("utf-8")
    req = urllib.request.Request(url, data=cuerpo, headers={"Content-Type": "application/json"})  # noqa: S310
    try:
        # LOCAL service: no proxy, or localhost bounces with HTTP_PROXY set.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=20) as r:
            datos = json.loads(r.read())
        emb = datos.get("embedding")
        return list(emb) if emb else None
    except Exception as e:  # degrading is the correct behavior
        logger.warning("Ollama unavailable for embeddings: %s", e)
        return None


def _embed_gemini(texto: str, modelo: str) -> list[float] | None:
    """Embedding via Gemini API. None when the key is no good."""
    clave = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not clave or not clave.startswith("AIza"):
        logger.warning("GEMINI_API_KEY does not look valid for embeddings")
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:embedContent?key={clave}"
    )
    cuerpo = json.dumps({"content": {"parts": [{"text": texto}]}}).encode("utf-8")
    req = urllib.request.Request(url, data=cuerpo, headers={"Content-Type": "application/json"})  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 - URL from trusted env config
            datos = json.loads(r.read())
        emb = datos.get("embedding", {}).get("values")
        return list(emb) if emb else None
    except Exception as e:  # degrading is the correct behavior
        logger.warning("Gemini embeddings failed: %s", e)
        return None


def _vec_extension_disponible() -> bool:
    """Probe for the optional sqlite-vec extension without importing it."""
    try:
        return importlib.util.find_spec("sqlite_vec") is not None
    except (ImportError, ValueError):
        return False


def _cargar_vec(con: sqlite3.Connection) -> None:
    """Load sqlite-vec into an open connection (extensions already enabled)."""
    vec = importlib.import_module("sqlite_vec")
    vec.load(con)


class Embedder:
    """Swappable embedding provider with explicit degradation."""

    def __init__(self, proveedor: str | None = None, modelo: str | None = None):
        self.proveedor = (
            (proveedor or os.getenv("MEMORY_EMBED_PROVIDER") or PROVEEDOR_DEFECTO).strip().lower()
        )
        self.modelo = modelo or os.getenv("MEMORY_EMBED_MODEL", "")
        self._dim: int | None = None
        self._degradado_a_hashing = False

    @property
    def dim(self) -> int:
        if self._dim is None:
            self.embed("dimension")  # pins the real dimension
        return self._dim or DIM_HASHING

    def embed(self, texto: str) -> list[float]:
        """Vector for the text. Never raises: falls back to hashing."""
        if self.proveedor == "ollama":
            v = _embed_ollama(texto, self.modelo or "nomic-embed-text")
            if v:
                self._dim = len(v)
                return v
            self._degradado_a_hashing = True
        elif self.proveedor == "gemini":
            v = _embed_gemini(texto, self.modelo or "text-embedding-004")
            if v:
                self._dim = len(v)
                return v
            self._degradado_a_hashing = True

        v = _embed_hashing(texto)
        self._dim = len(v)
        return v

    @property
    def degradado(self) -> bool:
        """True when a real provider was requested but hashing had to do."""
        return self._degradado_a_hashing

    def describe(self) -> dict[str, Any]:
        return {
            "proveedor": self.proveedor,
            "modelo": self.modelo or None,
            "dim": self.dim,
            "degradado_a_hashing": self.degradado,
        }


def _candidatos_semilla(max_files: int) -> list[Path]:
    """Collect markdown candidates for seeding (docs/ + root READMEs)."""
    candidatos: list[Path] = []
    for base in (_REPO_ROOT / "docs", _REPO_ROOT):
        if not base.exists():
            continue
        if base == _REPO_ROOT:
            for nombre in ("README.md", "AUDITORIA_V1.md", "apis_gratis.md"):
                p = base / nombre
                if p.is_file():
                    candidatos.append(p)
        else:
            candidatos.extend(sorted(base.glob("*.md"))[:max_files])
    return candidatos


# ── Vector layer ───────────────────────────────────────────


class MemorySemantic:
    """Vector index over ``rag_docs``, in a sqlite-vec virtual table."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        embedder: Embedder | None = None,
    ):
        self.db_path = Path(db_path) if db_path else resolve_db_path()
        self.embedder = embedder or Embedder()
        self._vec_disponible: bool | None = None

    def _con(self) -> sqlite3.Connection:
        if str(self.db_path) != ":memory:":
            parent = self.db_path.parent
            if str(parent):
                parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(self.db_path))
        if self._vec_disponible is None:
            self._vec_disponible = _vec_extension_disponible()
            if not self._vec_disponible:
                logger.warning(
                    "sqlite-vec not installed: semantic search unavailable "
                    "(MemoryVault keeps working). Install with: pip install sqlite-vec"
                )
        if self._vec_disponible:
            con.enable_load_extension(True)
            try:
                _cargar_vec(con)
            finally:
                con.enable_load_extension(False)
        return con

    def _tabla_existe(self, con: sqlite3.Connection, nombre: str = "rag_vecs") -> bool:
        """READ-ONLY schema check. Never creates anything.

        Separate from `_tabla_ok` because `search()` is a READ: if it called
        `_tabla_ok`, a plain query would create the virtual table and write
        to the database.
        """
        if not self._vec_disponible:
            return False
        return bool(
            con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (nombre,),
            ).fetchone()
        )

    def _tabla_ok(self, con: sqlite3.Connection) -> bool:
        """Create the virtual table if needed. WRITE only. False when
        sqlite-vec is unavailable."""
        if not self._vec_disponible:
            return False
        if self._tabla_existe(con):
            return True
        con.execute(
            f"CREATE VIRTUAL TABLE rag_vecs USING vec0(embedding float[{self.embedder.dim}])"
        )
        con.commit()
        return True

    # ── Escritura ──────────────────────────────────────────

    def index_doc(self, doc_id: int, content: str) -> bool:
        """Index (or reindex) one document. False when impossible."""
        con = self._con()
        try:
            if not self._tabla_ok(con):
                return False
            vec = self.embedder.embed(content or "")
            con.execute("DELETE FROM rag_vecs WHERE rowid = ?", (doc_id,))
            con.execute(
                "INSERT INTO rag_vecs (rowid, embedding) VALUES (?, ?)",
                (doc_id, json.dumps(vec)),
            )
            con.commit()
            return True
        finally:
            con.close()

    def index_all(self, lote: int = 200) -> dict[str, Any]:
        """Index every `rag_docs` row that has no vector yet."""
        con = self._con()
        try:
            if not self._tabla_ok(con):
                return {"ok": False, "motivo": "sqlite-vec no disponible", "indexados": 0}
            docs = con.execute("SELECT id, content FROM rag_docs").fetchall()
            ya = {r[0] for r in con.execute("SELECT rowid FROM rag_vecs").fetchall()}
            pendientes = [(i, c) for i, c in docs if i not in ya]
            indexados = 0
            for i, (doc_id, content) in enumerate(pendientes):
                vec = self.embedder.embed(content or "")
                con.execute("DELETE FROM rag_vecs WHERE rowid = ?", (doc_id,))
                con.execute(
                    "INSERT INTO rag_vecs (rowid, embedding) VALUES (?, ?)",
                    (doc_id, json.dumps(vec)),
                )
                indexados += 1
                if (i + 1) % lote == 0:
                    con.commit()
            con.commit()
            return {
                "ok": True,
                "indexados": indexados,
                "total_docs": len(docs),
                "ya_indexados": len(ya),
                "embedder": self.embedder.describe(),
            }
        finally:
            con.close()

    def reindex(self) -> dict[str, Any]:
        """Drop the index and rebuild. Mandatory when switching providers."""
        con = self._con()
        try:
            if not self._vec_disponible:
                return {"ok": False, "motivo": "sqlite-vec no disponible"}
            con.execute("DROP TABLE IF EXISTS rag_vecs")
            con.commit()
        finally:
            con.close()
        return self.index_all()

    def seed_from_docs(self, max_files: int = 40, max_chars: int = 4000) -> dict[str, Any]:
        """If rag_docs is empty, index markdown from docs/ + README.

        Without this, health says RAG empty forever even when the repo has
        documentation. Only inserts when count(rag_docs)==0 (idempotent).
        """
        con = self._con()
        try:
            con.execute(
                "CREATE TABLE IF NOT EXISTS rag_docs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "source TEXT, content TEXT, timestamp TEXT)"
            )
            con.commit()
            n = con.execute("SELECT COUNT(*) FROM rag_docs").fetchone()[0]
        finally:
            con.close()

        if n > 0:
            return {"ok": True, "sembrados": 0, "motivo": f"ya hay {n} docs"}

        candidatos = _candidatos_semilla(max_files)

        sembrados = 0
        ahora = datetime.now().isoformat()
        con = self._con()
        try:
            vistos = set()
            for path in candidatos:
                if path.resolve() in vistos:
                    continue
                vistos.add(path.resolve())
                try:
                    texto = path.read_text(encoding="utf-8", errors="ignore").strip()
                except OSError:
                    continue
                if len(texto) < MIN_DOC_CHARS:
                    continue
                con.execute(
                    "INSERT INTO rag_docs (source, content, timestamp) VALUES (?,?,?)",
                    (str(path.relative_to(_REPO_ROOT)), texto[:max_chars], ahora),
                )
                sembrados += 1
                if sembrados >= max_files:
                    break
            con.commit()
        finally:
            con.close()

        indexado = self.index_all() if sembrados else {"ok": True, "indexados": 0}
        return {"ok": True, "sembrados": sembrados, "index": indexado}

    # ── Lectura ────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Nearest neighbours by semantic similarity.

        Returns [] (not an exception) when the index is unavailable: the
        caller should fall back to the MemoryVault lexical `recall()`.
        """
        if not (query or "").strip():
            return []
        con = self._con()
        try:
            # _tabla_existe, NOT _tabla_ok: a search must not create schema.
            if not self._tabla_existe(con):
                return []
            qvec = self.embedder.embed(query)
            if len(qvec) != self.embedder.dim:
                logger.warning("Dimension mismatch between query and index")
                return []
            filas = con.execute(
                "SELECT rowid, distance FROM rag_vecs "
                "WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
                (json.dumps(qvec), int(top_k)),
            ).fetchall()
            if not filas:
                return []
            ids = [f[0] for f in filas]
            dist = {f[0]: f[1] for f in filas}
            marcas = ",".join("?" * len(ids))
            meta = con.execute(
                f"SELECT id, source, content, timestamp FROM rag_docs WHERE id IN ({marcas})",  # noqa: S608 - placeholders only
                tuple(ids),
            ).fetchall()
            por_id = {m[0]: m for m in meta}
            salida = []
            for doc_id in ids:  # preserve distance order
                m = por_id.get(doc_id)
                if not m:
                    continue
                d = float(dist[doc_id])
                salida.append(
                    {
                        "id": doc_id,
                        "source": m[1],
                        "content": (m[2] or "")[:600],
                        "timestamp": m[3],
                        "score": round(_l2_a_coseno(d), 3),
                        "distance": round(d, 4),
                        "via": "vectorial",
                    }
                )
            return salida
        finally:
            con.close()

    def search_hybrid(
        self, query: str, top_k: int = 5, peso_vector: float = 0.6
    ) -> list[dict[str, Any]]:
        """Combine vault lexical recall with vector search.

        The vector catches fuzzy similarity, the vault adds the graph
        (neighbours that don't look alike but are related).
        """
        vectorial = self.search(query, top_k=top_k)
        try:
            lexicos = MemoryVault(self.db_path).recall(query, top_k=top_k)
        except Exception as e:  # lexical failure must not kill hybrid
            logger.warning("lexical recall failed: %s", e)
            return vectorial

        fusion: dict[int, dict[str, Any]] = {}
        for r in vectorial:
            fusion[r["id"]] = dict(r, score=round(r["score"] * peso_vector, 3))
        for r in lexicos:
            rid = r.get("id")
            if rid in fusion:
                fusion[rid]["score"] = round(
                    fusion[rid]["score"] + r.get("score", 0) * (1 - peso_vector), 3
                )
                fusion[rid]["via"] = "vectorial+lexico"
            else:
                fusion[rid] = dict(
                    r,
                    score=round(r.get("score", 0) * (1 - peso_vector), 3),
                    via=f"lexico/{r.get('via', '')}",
                )
        ordenados = sorted(fusion.values(), key=lambda d: d["score"], reverse=True)
        return ordenados[: max(1, top_k)]

    def stats(self) -> dict[str, Any]:
        con = self._con()
        try:
            docs = (
                con.execute("SELECT COUNT(*) FROM rag_docs").fetchone()[0]
                if con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='rag_docs'"
                ).fetchone()
                else 0
            )
            idx = 0
            if (
                self._vec_disponible
                and con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='rag_vecs'"
                ).fetchone()
            ):
                idx = con.execute("SELECT COUNT(*) FROM rag_vecs").fetchone()[0]
        finally:
            con.close()
        return {
            "db": str(self.db_path),
            "sqlite_vec": bool(self._vec_disponible),
            "docs_en_vault": docs,
            "docs_indexados": idx,
            "pendientes_de_indexar": max(0, docs - idx),
            "embedder": self.embedder.describe(),
        }


# ── Singleton (repo pattern) ─────────────────────────────────

_INSTANCIA: MemorySemantic | None = None


def get_instance() -> MemorySemantic:
    """Single instance, like the rest of the repo modules."""
    global _INSTANCIA  # noqa: PLW0603 - repo-wide singleton pattern
    if _INSTANCIA is None:
        _INSTANCIA = MemorySemantic()
    return _INSTANCIA


# ── CLI ──────────────────────────────────────────────────────


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Memory Semantic (canonical)")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("index", help="Index all unindexed docs")
    p_search = sub.add_parser("search", help="Vector search")
    p_search.add_argument("query")
    p_search.add_argument("--top", type=int, default=5)
    sub.add_parser("reindex", help="Drop and rebuild the index")
    sub.add_parser("stats", help="Stats")

    args = parser.parse_args(argv)
    sem = get_instance()

    if args.cmd == "index":
        print(json.dumps(sem.index_all(), indent=2, ensure_ascii=False))  # noqa: T201 - CLI output
    elif args.cmd == "search":
        for r in sem.search(args.query, top_k=args.top):
            print(  # noqa: T201 - CLI output
                f"[{r['score']:.2f} {r['via']:8}] #{r['id']} ({r['source']}): "
                f"{r['content'][:100]}..."
            )
    elif args.cmd == "reindex":
        print(json.dumps(sem.reindex(), indent=2, ensure_ascii=False))  # noqa: T201 - CLI output
    elif args.cmd == "stats":
        print(json.dumps(sem.stats(), indent=2, ensure_ascii=False))  # noqa: T201 - CLI output
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

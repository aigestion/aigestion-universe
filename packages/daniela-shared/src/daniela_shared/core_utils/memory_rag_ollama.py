"""
E-35: Memory RAG — Retrieval-Augmented Generation with Ollama embeddings.

Indexes documents and provides semantic search using:
- Ollama nomic-embed-text for vectorization
- SQLite for metadata storage
- Python cosine similarity for search (no sqlite-vec dependency)

Endpoints:
  POST /api/memory/index     — index a document or text chunk
  POST /api/memory/search    — semantic search
  GET  /api/memory/status    — index stats
  POST /api/memory/reindex   — reindex all docs/ files
"""

import glob
import hashlib
import json
import os
import sqlite3
import time
import urllib.request
from pathlib import Path

from flask import Blueprint, jsonify, request

memory_bp = Blueprint("memory", __name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Raiz por MARCADOR: con tres `dirname` se llegaba a la raiz cuando este
# fichero vivia en `<repo>/daniela-os/shared/`; al entrar en
# `gev/daniela-os/shared/` los tres `dirname` dan `<repo>/gev` y la
# memoria RAG se abria en `gev/data/memory_rag.db` (otra base nueva,
# vacia, con el historial bueno a un nivel de distancia).
def _repo_root() -> str:
    aqui = Path(os.path.abspath(__file__))
    for c in (aqui.parent, *aqui.parents):
        if (c / ".git").exists() or (c / "tests" / "conftest.py").exists():
            return str(c)
    return os.path.dirname(os.path.dirname(os.path.dirname(str(aqui))))


REPO_ROOT = _repo_root()
# In Docker, /app/data is writable; locally, use repo data/
DATA_DIR = os.getenv("DATA_DIR", os.path.join(REPO_ROOT, "data"))
DB_PATH = os.path.join(DATA_DIR, "memory_rag.db")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 50

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = _get_db()
    # Migration: if doc_id column missing, recreate table
    cols = [r[1] for r in conn.execute("PRAGMA table_info(rag_docs)").fetchall()] if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rag_docs'").fetchone() else []
    if cols and "doc_id" not in cols:
        conn.executescript("""
            CREATE TABLE rag_docs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT UNIQUE,
                source TEXT,
                title TEXT,
                content TEXT,
                chunk_index INTEGER DEFAULT 0,
                embedding BLOB,
                created_at REAL,
                content_hash TEXT
            );
            INSERT OR IGNORE INTO rag_docs_new (id, source, content)
            SELECT id, source, content FROM rag_docs;
            DROP TABLE rag_docs;
            ALTER TABLE rag_docs_new RENAME TO rag_docs;
        """)
        conn.commit()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rag_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT UNIQUE,
            source TEXT,
            title TEXT,
            content TEXT,
            chunk_index INTEGER DEFAULT 0,
            embedding BLOB,
            created_at REAL,
            content_hash TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_rag_docs_source ON rag_docs(source);
        CREATE INDEX IF NOT EXISTS idx_rag_docs_doc_id ON rag_docs(doc_id);

        CREATE TABLE IF NOT EXISTS memory_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT,
            to_id TEXT,
            relation TEXT,
            created_at REAL
        );
    """)
    conn.close()


# ---------------------------------------------------------------------------
# Embeddings via Ollama
# ---------------------------------------------------------------------------

def _embed(texts):
    """Generate embeddings via Ollama /api/embed."""
    url = f"{OLLAMA_URL}/api/embed"
    payload = json.dumps({"model": EMBED_MODEL, "input": texts}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode("utf-8"))
    return data.get("embeddings", [])


def _cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start + overlap >= len(text):
            break
    return chunks


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@memory_bp.route("/api/memory/status")
def memory_status():
    """Index statistics."""
    _init_db()
    conn = _get_db()
    try:
        doc_count = conn.execute("SELECT COUNT(*) FROM rag_docs").fetchone()[0]
        source_counts = {}
        for row in conn.execute("SELECT source, COUNT(*) as cnt FROM rag_docs GROUP BY source"):
            source_counts[row["source"]] = row["cnt"]
        link_count = conn.execute("SELECT COUNT(*) FROM memory_links").fetchone()[0]
    finally:
        conn.close()

    return jsonify({
        "rag_docs": doc_count,
        "memory_links": link_count,
        "sources": source_counts,
        "db_path": DB_PATH,
        "embed_model": EMBED_MODEL,
        "ollama_url": OLLAMA_URL,
    })


@memory_bp.route("/api/memory/index", methods=["POST"])
def memory_index():
    """
    Index a document or text.

    Body: {"text": "...", "source": "doc_name", "title": "optional"}
    """
    data = request.json or {}
    text = (data.get("text") or "").strip()
    source = data.get("source", "manual")
    title = data.get("title", "")

    if not text:
        return jsonify({"error": "text requerido"}), 400

    _init_db()
    conn = _get_db()

    try:
        # Chunk the text
        chunks = _chunk_text(text)
        if not chunks:
            return jsonify({"error": "texto vacio despues de chunking"}), 400

        # Generate embeddings
        try:
            embeddings = _embed(chunks)
        except Exception as e:
            return jsonify({"error": f"Embedding failed: {str(e)[:200]}"}), 502

        if len(embeddings) != len(chunks):
            return jsonify({"error": "Embedding count mismatch"}), 502

        # Store in DB
        now = time.time()
        indexed = 0
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            content_hash = hashlib.md5(chunk.encode()).hexdigest()
            doc_id = f"{source}#{i}#{content_hash[:8]}"

            # Upsert
            existing = conn.execute("SELECT id FROM rag_docs WHERE doc_id = ?", (doc_id,)).fetchone()
            blob = json.dumps(embedding).encode("utf-8")
            if existing:
                conn.execute(
                    "UPDATE rag_docs SET content=?, embedding=?, created_at=?, content_hash=? WHERE doc_id=?",
                    (chunk, blob, now, content_hash, doc_id),
                )
            else:
                conn.execute(
                    "INSERT INTO rag_docs (doc_id, source, title, content, chunk_index, embedding, created_at, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (doc_id, source, title, chunk, i, blob, now, content_hash),
                )
            indexed += 1

        conn.commit()
        return jsonify({
            "indexed": indexed,
            "source": source,
            "chunks": len(chunks),
            "total_docs": conn.execute("SELECT COUNT(*) FROM rag_docs").fetchone()[0],
        })
    finally:
        conn.close()


@memory_bp.route("/api/memory/search", methods=["POST"])
def memory_search():
    """
    Semantic search.

    Body: {"query": "...", "top_k": 5, "source_filter": "optional"}
    """
    data = request.json or {}
    query = (data.get("query") or "").strip()
    top_k = min(data.get("top_k", 5), 20)
    source_filter = data.get("source_filter")

    if not query:
        return jsonify({"error": "query requerido"}), 400

    _init_db()
    conn = _get_db()

    try:
        # Embed the query
        try:
            query_embedding = _embed([query])[0]
        except Exception as e:
            return jsonify({"error": f"Embedding failed: {str(e)[:200]}"}), 502

        # Fetch all docs (for small indexes this is fine)
        sql = "SELECT doc_id, source, title, content, chunk_index, embedding FROM rag_docs"
        params = []
        if source_filter:
            sql += " WHERE source = ?"
            params.append(source_filter)

        rows = conn.execute(sql, params).fetchall()

        # Compute similarities
        results = []
        for row in rows:
            try:
                doc_embedding = json.loads(row["embedding"].decode("utf-8") if isinstance(row["embedding"], bytes) else row["embedding"])
                score = _cosine_similarity(query_embedding, doc_embedding)
                results.append({
                    "doc_id": row["doc_id"],
                    "source": row["source"],
                    "title": row["title"],
                    "content": row["content"],
                    "chunk_index": row["chunk_index"],
                    "score": round(score, 4),
                })
            except Exception:
                continue

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

        return jsonify({
            "query": query,
            "results": results,
            "count": len(results),
            "total_indexed": len(rows),
        })
    finally:
        conn.close()


@memory_bp.route("/api/memory/reindex", methods=["POST"])
def memory_reindex():
    """
    Reindex all docs/ files into the RAG.

    Scans docs/ directory for .md and .txt files, chunks and indexes them.
    """
    _init_db()
    docs_dir = os.path.join(REPO_ROOT, "docs")
    if not os.path.isdir(docs_dir):
        return jsonify({"error": f"docs/ directory not found at {docs_dir}"}), 404

    conn = _get_db()
    total_indexed = 0
    files_processed = 0
    errors = []

    try:
        for filepath in glob.glob(os.path.join(docs_dir, "**/*.md"), recursive=True) + \
                         glob.glob(os.path.join(docs_dir, "**/*.txt"), recursive=True):
            try:
                with open(filepath, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                if not text.strip():
                    continue

                rel_path = os.path.relpath(filepath, REPO_ROOT)
                chunks = _chunk_text(text)
                if not chunks:
                    continue

                embeddings = _embed(chunks)
                now = time.time()

                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    content_hash = hashlib.md5(chunk.encode()).hexdigest()
                    doc_id = f"{rel_path}#{i}#{content_hash[:8]}"
                    blob = json.dumps(embedding).encode("utf-8")

                    existing = conn.execute("SELECT id FROM rag_docs WHERE doc_id = ?", (doc_id,)).fetchone()
                    if existing:
                        conn.execute(
                            "UPDATE rag_docs SET content=?, embedding=?, created_at=?, content_hash=? WHERE doc_id=?",
                            (chunk, blob, now, content_hash, doc_id),
                        )
                    else:
                        conn.execute(
                            "INSERT INTO rag_docs (doc_id, source, title, content, chunk_index, embedding, created_at, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (doc_id, rel_path, os.path.basename(filepath), chunk, i, blob, now, content_hash),
                        )
                    total_indexed += 1

                files_processed += 1
            except Exception as e:
                errors.append(f"{filepath}: {str(e)[:100]}")

        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "files_processed": files_processed,
        "chunks_indexed": total_indexed,
        "errors": errors,
        "total_docs": total_indexed,
    })


_init_db()

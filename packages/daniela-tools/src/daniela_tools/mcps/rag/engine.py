"""RAG engine: ingestion, retrieval and grounded answers."""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence

from .chunking import DEFAULT_MAX_CHARS, DEFAULT_OVERLAP, chunk_document
from .embedding import BaseEmbedder, LsaEmbedder, build_embedder
from .generation import Answer, compose_answer, format_sources
from .retrieval import HybridRetriever, ScoredChunk
from .store import DEFAULT_DB_PATH, DocumentStore

__all__ = ["RAGEngine", "RAGConfig"]


class RAGConfig:
    """Tunable knobs, kept in one place so the dashboard can report them."""

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        max_chunk_chars: int = DEFAULT_MAX_CHARS,
        chunk_overlap: int = DEFAULT_OVERLAP,
        top_k: int = 5,
        rrf_k: int = 60,
        lexical_weight: float = 1.0,
        semantic_weight: float = 1.0,
        n_components: int = 128,
        prefer_transformers: bool = True,
        embedder: BaseEmbedder | None = None,
        generator: Callable[[str, Sequence[dict]], str] | None = None,
    ):
        self.db_path = db_path
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.rrf_k = rrf_k
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight
        self.n_components = n_components
        self.prefer_transformers = prefer_transformers
        self.embedder = embedder
        self.generator = generator

    def to_dict(self) -> dict:
        return {
            "db_path": self.db_path,
            "max_chunk_chars": self.max_chunk_chars,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "rrf_k": self.rrf_k,
            "lexical_weight": self.lexical_weight,
            "semantic_weight": self.semantic_weight,
            "n_components": self.n_components,
            "prefer_transformers": self.prefer_transformers,
        }


class RAGEngine:
    """Retrieval-augmented generation over a SQLite document store.

    Typical use::

        engine = RAGEngine()
        engine.ingest_text("Guia", "El agente 1 orquesta ...", doc_id="guia")
        results = engine.retrieve("que orquesta el agente 1")
        answer = engine.answer("que orquesta el agente 1")
    """

    def __init__(self, config: RAGConfig | None = None, store: DocumentStore | None = None):
        self.config = config or RAGConfig()
        self.store = store or DocumentStore(self.config.db_path)

        embedder = self.config.embedder
        if embedder is None:
            embedder = (
                build_embedder(prefer_transformers=self.config.prefer_transformers)
                if self.config.prefer_transformers
                else LsaEmbedder(n_components=self.config.n_components)
            )
        self.embedder = embedder
        self.retriever = HybridRetriever(
            embedder,
            rrf_k=self.config.rrf_k,
            lexical_weight=self.config.lexical_weight,
            semantic_weight=self.config.semantic_weight,
        )

        self._chunks: list[dict] = []
        self._lock = threading.RLock()
        self._indexed = False
        # With no generator configured, fall back to an environment-provided
        # one. Failing that, the extractive path answers on its own, so the
        # engine stays useful without any credentials.
        if self.config.generator is None:
            try:
                from .generators import generator_from_env

                self.config.generator = generator_from_env()
            except Exception:
                self.config.generator = None
        self._stats = {"ingested": 0, "queries": 0, "cache_hits": 0, "rebuilds": 0}

    # -- ingestion -------------------------------------------------------
    def ingest_text(
        self,
        content: str,
        title: str = "",
        *,
        doc_id: str | None = None,
        category: str = "general",
        source: str = "",
        rebuild: bool = True,
    ) -> int:
        """Add one document. Returns the number of chunks created."""
        title = title or "Untitled"
        doc_id = doc_id or self._derive_doc_id(title, content)
        self.store.upsert_document(doc_id, title, content, category, source)
        chunks = chunk_document(
            content,
            title,
            doc_id=doc_id,
            category=category,
            source=source,
            max_chars=self.config.max_chunk_chars,
            overlap=self.config.chunk_overlap,
        )
        count = self.store.replace_chunks(doc_id, chunks)
        self._stats["ingested"] += 1
        if rebuild:
            self.rebuild()
        return count

    def ingest_many(self, documents: Sequence[dict[str, object]], rebuild: bool = True) -> int:
        """Add several documents at once, rebuilding the index once at the end."""
        total = 0
        for document in documents:
            total += self.ingest_text(
                str(document.get("content", "")),
                str(document.get("title", "")),
                doc_id=document.get("doc_id") or None,  # type: ignore[arg-type]
                category=str(document.get("category", "general")),
                source=str(document.get("source", "")),
                rebuild=False,
            )
        if rebuild:
            self.rebuild()
        return total

    def ingest_directory(self, directory: str, pattern: str = "*.md", rebuild: bool = True) -> int:
        """Ingest every matching text file, using its stem as the document id."""
        import pathlib

        base = pathlib.Path(directory)
        if not base.is_dir():
            return 0
        documents = []
        for path in sorted(base.rglob(pattern)):
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            documents.append(
                {
                    "doc_id": str(path.relative_to(base)),
                    "title": path.stem.replace("_", " ").title(),
                    "content": content,
                    "category": path.parent.name or "general",
                    "source": str(path),
                }
            )
        return self.ingest_many(documents, rebuild=rebuild)

    @staticmethod
    def _derive_doc_id(title: str, content: str) -> str:
        import hashlib

        digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in title).strip("-")
        slug = "-".join(part for part in slug.split("-") if part)[:48] or "document"
        return f"{slug}-{digest}"

    def delete(self, doc_id: str, rebuild: bool = True) -> None:
        self.store.delete_document(doc_id)
        if rebuild:
            self.rebuild()

    # -- index -----------------------------------------------------------
    def rebuild(self, category: str | None = None) -> int:
        """Reload chunks from storage and refit both retrievers."""
        with self._lock:
            chunks = self.store.load_chunks(category=category)
            self._chunks = chunks
            self.retriever.fit(chunks)
            self._indexed = True
            self._stats["rebuilds"] += 1
            return len(chunks)

    # Backwards-compatible alias.
    build_index = rebuild

    # -- retrieval -------------------------------------------------------
    def retrieve(
        self, query: str, top_k: int | None = None, category: str | None = None
    ) -> list[ScoredChunk]:
        """Return the chunks most relevant to ``query``."""
        top_k = top_k or self.config.top_k
        if not (query or "").strip():
            return []
        if not self._indexed:
            self.rebuild(category=category)
        self._stats["queries"] += 1
        results = self.retriever.search(query, top_k=top_k)
        if category:
            results = [r for r in results if r.chunk.get("category") == category]
        return results

    def retrieve_relevant_docs(self, query: str, top_k: int | None = None) -> list[dict]:
        """Retrieve chunks as plain dicts."""
        return [result.to_dict() for result in self.retrieve(query, top_k=top_k)]

    # -- answers ---------------------------------------------------------
    def answer(self, query: str, top_k: int | None = None) -> Answer:
        """Retrieve, then compose a grounded answer."""
        results = self.retrieve(query, top_k=top_k)
        return compose_answer(query, results, generator=self.config.generator)

    def generate_response(
        self, query: str, context: Sequence[dict] | None = None, top_k: int | None = None
    ) -> str:
        """Answer ``query``, preferring caller-supplied ``context``.

        Unlike the previous implementation, the ``context`` argument is actually
        honoured: when documents are supplied they are used instead of running
        retrieval, so callers can answer against evidence they already hold.
        """
        if context:
            chunks = [dict(c) for c in context]
            results = [
                ScoredChunk(chunk=chunk, score=1.0 - index * 0.01, sources=["provided"])
                for index, chunk in enumerate(chunks)
            ]
            return compose_answer(query, results, generator=self.config.generator).text
        return self.answer(query, top_k=top_k).text

    def augment_with_context(self, query: str, top_k: int | None = None) -> str:
        """Build a context block for ``query``, ready to prepend to a prompt."""
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return f"No relevant context found for query: {query}"
        context = "\n\n".join(
            f"[{i}] {r.chunk.get('title', '')}\n{r.chunk.get('content', '')}"
            for i, r in enumerate(results, start=1)
        )
        return f"Query: {query}\nContext:\n{context}"

    def citations(self, query: str, top_k: int | None = None) -> str:
        return format_sources(self.retrieve(query, top_k=top_k))

    # -- diagnostics -----------------------------------------------------
    def stats(self) -> dict:
        """Retrieval and storage counters, for the dashboard.

        ``indexed_chunks`` counts what is loaded in memory; ``stored_chunks``
        counts what is persisted. They differ until the first query triggers a
        lazy rebuild, so both are reported rather than only the flattering one.
        """
        with self._lock:
            stats = dict(self._stats)
            stats.update(
                {
                    "indexed_chunks": len(self._chunks),
                    "stored_chunks": self.store.stats()["chunks"],
                    "indexed": self._indexed,
                    "embedding_backend": getattr(self.embedder, "backend", self.embedder.name),
                    "embedding_dim": self.embedder.dim,
                    "retrieval": "hybrid (bm25 + dense, rrf)",
                    "generator": type(self.config.generator).__name__
                    if self.config.generator
                    else "extractive",
                }
            )
            stats.update(self.store.stats())
            return stats

    @property
    def config_summary(self) -> dict:
        return self.config.to_dict()

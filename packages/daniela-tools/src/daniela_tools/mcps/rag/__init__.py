"""Retrieval-Augmented Generation for the AI system.

Public surface::

    from mcps.rag import RAGEngine, get_rag_engine, retrieve_documents

The engine combines BM25 lexical scoring with dense vector search (transformer
embeddings when a backend is available, otherwise TF-IDF + SVD over NumPy),
fuses the two rankings with Reciprocal Rank Fusion, and composes an extractive
answer with citations from the retrieved passages.
"""

from __future__ import annotations

from collections.abc import Sequence

from .chunking import DEFAULT_MAX_CHARS, DEFAULT_OVERLAP, chunk_document, chunk_text
from .embedding import (
    BaseEmbedder,
    LsaEmbedder,
    SentenceTransformerEmbedder,
    available_backends,
    build_embedder,
)
from .engine import RAGConfig, RAGEngine
from .generation import Answer, compose_answer, format_sources
from .generators import GeneratorError, OpenRouterGenerator, generator_from_env
from .lexicon import PHRASES, TOKEN_EQUIVALENTS, expand_bilingual
from .retrieval import Bm25Retriever, DenseRetriever, HybridRetriever, ScoredChunk
from .store import DEFAULT_DB_PATH, DocumentStore
from .text import normalize, stem, tokenize

__all__ = [
    "RAGEngine",
    "RAGConfig",
    "DocumentStore",
    "DEFAULT_DB_PATH",
    "Answer",
    "ScoredChunk",
    "Bm25Retriever",
    "DenseRetriever",
    "HybridRetriever",
    "BaseEmbedder",
    "LsaEmbedder",
    "SentenceTransformerEmbedder",
    "build_embedder",
    "available_backends",
    "chunk_text",
    "chunk_document",
    "compose_answer",
    "format_sources",
    "OpenRouterGenerator",
    "GeneratorError",
    "generator_from_env",
    "DEFAULT_MAX_CHARS",
    "DEFAULT_OVERLAP",
    "normalize",
    "stem",
    "tokenize",
    "PHRASES",
    "TOKEN_EQUIVALENTS",
    "expand_bilingual",
    "get_rag_engine",
    "retrieve_documents",
    "generate_response",
    "augment_with_context",
    "rag_engine",
]

# Process-wide engine, created lazily so importing this module never touches
# the database or loads a model.
_engine: RAGEngine | None = None


def get_rag_engine(config: RAGConfig | None = None) -> RAGEngine:
    """Return the shared engine, creating it on first use."""
    global _engine
    if config is not None:
        _engine = RAGEngine(config)
    elif _engine is None:
        _engine = RAGEngine()
    return _engine


# Retained for callers of the previous API.
def get_ragged_engine() -> RAGEngine:
    return get_rag_engine()


def retrieve_documents(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve relevant chunks for ``query``."""
    return get_rag_engine().retrieve_relevant_docs(query, top_k=top_k)


def generate_response(
    query: str, context: Sequence[dict] | None = None, top_k: int = 5
) -> str:
    """Answer ``query``, using ``context`` when supplied."""
    return get_rag_engine().generate_response(query, context=context, top_k=top_k)


def augment_with_context(query: str, top_k: int = 5) -> str:
    return get_rag_engine().augment_with_context(query, top_k=top_k)


class _LazyEngine:
    """Module attribute that behaves like an engine but defers construction."""

    def __getattr__(self, name: str):
        return getattr(get_rag_engine(), name)

    def __repr__(self) -> str:
        state = "uninitialised" if _engine is None else "ready"
        return f"<lazy RAGEngine ({state})>"


rag_engine = _LazyEngine()

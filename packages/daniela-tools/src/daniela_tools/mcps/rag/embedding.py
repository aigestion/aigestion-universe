"""Vector embeddings for semantic retrieval.

Two backends are provided behind one interface:

``LsaEmbedder``
    Pure NumPy. TF-IDF vectors projected onto the top ``n_components``
    singular vectors of the term-document matrix (latent semantic analysis).
    Fast, offline, and good enough that "agente que coordina" reaches a chunk
    that never uses the word "coordina" verbatim.

``SentenceTransformerEmbedder``
    Real transformer embeddings, used when a backend and a local model are
    available. Falls back to LSA instead of raising.

Both expose ``fit(corpus)`` and ``encode(texts) -> ndarray`` so
``HybridRetriever`` does not care which one it got.
"""

from __future__ import annotations

import math
import threading
from collections.abc import Iterable, Sequence

import numpy as np

from .text import tokenize

__all__ = [
    "BaseEmbedder",
    "LsaEmbedder",
    "SentenceTransformerEmbedder",
    "build_embedder",
]


class BaseEmbedder:
    """Common interface: ``fit`` then ``encode``."""

    name = "base"

    def fit(self, corpus: Sequence[str]) -> BaseEmbedder:
        raise NotImplementedError

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        raise NotImplementedError

    @property
    def dim(self) -> int:
        raise NotImplementedError


class LsaEmbedder(BaseEmbedder):
    """TF-IDF + truncated SVD using only NumPy."""

    name = "lsa"

    def __init__(self, n_components: int = 128, min_df: int = 1, max_df: float = 1.0):
        self.n_components = n_components
        self.min_df = min_df
        self.max_df = max_df
        self._vocabulary: dict[str, int] = {}
        self._idf: np.ndarray = np.zeros(0)
        self._components: np.ndarray = np.zeros((0, 0))
        self._doc_vectors: np.ndarray | None = None
        self._lock = threading.Lock()

    # -- fitting ---------------------------------------------------------
    def fit(self, corpus: Sequence[str]) -> LsaEmbedder:
        """Build the vocabulary and latent basis from ``corpus``."""
        tokenized = [tokenize(text) for text in corpus]
        if not tokenized:
            self._vocabulary, self._idf = {}, np.zeros(0)
            self._components = np.zeros((0, 0))
            self._doc_vectors = np.zeros((0, 0))
            return self

        # Document frequency, used to prune terms that carry no signal.
        doc_freq: dict[str, int] = {}
        for tokens in tokenized:
            for term in set(tokens):
                doc_freq[term] = doc_freq.get(term, 0) + 1

        n_docs = len(tokenized)
        min_count = self.min_df
        max_count = self.max_df * n_docs if self.max_df <= 1.0 else self.max_df

        # Sort terms for a deterministic vocabulary index.
        vocabulary = sorted(
            term
            for term, count in doc_freq.items()
            if min_count <= count and count <= max_count
        )
        self._vocabulary = {term: i for i, term in enumerate(vocabulary)}

        if not self._vocabulary:
            self._idf = np.zeros(0)
            self._components = np.zeros((0, 0))
            self._doc_vectors = np.zeros((n_docs, 0))
            return self

        self._idf = np.array(
            [math.log((1 + n_docs) / (1 + doc_freq[term])) + 1.0 for term in vocabulary]
        )
        tfidf = self._tfidf_matrix(tokenized, n_docs)
        self._components = self._truncated_svd(tfidf)
        self._doc_vectors = self._project(tfidf)
        return self

    def _tfidf_matrix(self, tokenized: list[list[str]], n_rows: int) -> np.ndarray:
        matrix = np.zeros((n_rows, len(self._vocabulary)), dtype=np.float64)
        for row, tokens in enumerate(tokenized):
            if not tokens:
                continue
            counts: dict[int, int] = {}
            for term in tokens:
                column = self._vocabulary.get(term)
                if column is not None:
                    counts[column] = counts.get(column, 0) + 1
            if not counts:
                continue
            # Sublinear TF dampens repeated boilerplate.
            for column, count in counts.items():
                matrix[row, column] = (1.0 + math.log(count)) * self._idf[column]
        # L2-normalize rows so cosine similarity is a plain dot product.
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        np.divide(matrix, norms, out=matrix, where=norms > 0)
        return matrix

    def _truncated_svd(self, matrix: np.ndarray) -> np.ndarray:
        """Right singular vectors, i.e. the term x component projection basis."""
        if matrix.size == 0:
            return np.zeros((matrix.shape[1], 0))
        n_components = min(self.n_components, min(matrix.shape) - 1)
        if n_components < 1:
            return np.eye(matrix.shape[1])
        # Full SVD is acceptable at this corpus size and avoids the
        # convergence tuning that randomised methods would need.
        _, singular, vt = np.linalg.svd(matrix, full_matrices=False)
        del singular
        return vt[:n_components].T

    def _project(self, tfidf: np.ndarray) -> np.ndarray:
        if self._components.size == 0:
            return np.zeros((tfidf.shape[0], 0))
        projected = tfidf @ self._components
        return _l2_normalize(projected)

    # -- inference -------------------------------------------------------
    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """Project ``texts`` onto the fitted latent space."""
        with self._lock:
            components = self._components
            if components.size == 0:
                return np.zeros((len(texts), 0))
            tokenized = [tokenize(text) for text in texts]
            tfidf = self._tfidf_matrix(tokenized, len(texts))
            return self._project(tfidf)

    @property
    def dim(self) -> int:
        return self._components.shape[1] if self._components.size else 0

    @property
    def document_vectors(self) -> np.ndarray:
        """Precomputed vectors for the fitted corpus."""
        if self._doc_vectors is None:
            return np.zeros((0, self.dim))
        return self._doc_vectors


class SentenceTransformerEmbedder(BaseEmbedder):
    """Transformer embeddings when available, LSA otherwise."""

    name = "sentence-transformers"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", fallback: BaseEmbedder | None = None):
        self.model_name = model_name
        self._model = None
        self._fallback = fallback
        self._backend: str = "unavailable"
        self._lock = threading.Lock()

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                # Import lazily: a missing optional backend must not break import.
                from sentence_transformers import SentenceTransformer

                model = SentenceTransformer(self.model_name)
            except Exception:
                return None
            self._model = model
            self._backend = self.model_name
            return model

    @property
    def backend(self) -> str:
        """Name of the backend actually in use."""
        if self._ensure_model() is not None:
            return self.model_name
        return "lsa-fallback"

    def fit(self, corpus: Sequence[str]) -> SentenceTransformerEmbedder:
        model = self._ensure_model()
        if model is None:
            if self._fallback is None:
                self._fallback = LsaEmbedder().fit(corpus)
            else:
                self._fallback.fit(corpus)
        return self

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        model = self._ensure_model()
        if model is None:
            if self._fallback is None:
                self._fallback = LsaEmbedder().fit(list(texts))
            return self._fallback.encode(texts)
        vectors = model.encode(
            list(texts), convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(vectors, dtype=np.float64)

    @property
    def dim(self) -> int:
        model = self._ensure_model()
        if model is None:
            return self._fallback.dim if self._fallback else 0
        return int(model.get_sentence_embedding_dimension())


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return np.divide(matrix, norms, out=matrix, where=norms > 0)


def build_embedder(prefer_transformers: bool = True, model_name: str = "all-MiniLM-L6-v2") -> BaseEmbedder:
    """Pick the strongest embedder that actually works in this environment.

    Sentence-transformers needs a backend (PyTorch or ONNX) that may be absent.
    Probing is done here once so retrieval never pays the cost later.
    """
    if prefer_transformers:
        candidate = SentenceTransformerEmbedder(model_name=model_name)
        if candidate._ensure_model() is not None:
            return candidate
    return LsaEmbedder()


def available_backends() -> list[str]:
    """Report which embedding backends can be used, for diagnostics."""
    found = []
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401

        found.append("sentence-transformers")
    except Exception:
        pass
    try:
        import numpy  # noqa: F401

        found.append("lsa")
    except Exception:
        pass
    return found


def iter_texts(chunks: Iterable[dict]) -> list[str]:
    """Extract indexable text from chunk records."""
    return [
        str(chunk.get("indexed_text") or chunk.get("content") or "") for chunk in chunks
    ]

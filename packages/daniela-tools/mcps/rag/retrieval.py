"""Retrievers and rank fusion.

BM25 alone misses paraphrases ("agente que coordina" vs "orquesta los
subsistemas"); dense vectors alone miss rare exact terms ("subagent_17").
``HybridRetriever`` runs both and fuses the ranked lists with Reciprocal Rank
Fusion, which needs no score calibration between the two.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from .embedding import BaseEmbedder
from .lexicon import expand_bilingual
from .text import (
    expand_query,
    expand_query_fuzzy,
    query_is_coherent,
    set_vocabulary_snapshot,
    tokenize,
)

__all__ = [
    "ScoredChunk",
    "Bm25Retriever",
    "DenseRetriever",
    "HybridRetriever",
    "reciprocal_rank_fusion",
]


@dataclass
class ScoredChunk:
    """A chunk with its score and which retrievers found it."""

    chunk: dict
    score: float
    lexical_score: float = 0.0
    semantic_score: float = 0.0
    sources: list[str] = field(default_factory=list)

    @property
    def doc_id(self) -> str:
        return str(self.chunk.get("doc_id", ""))

    def to_dict(self) -> dict:
        return {
            **self.chunk,
            "score": round(self.score, 6),
            "lexical_score": round(self.lexical_score, 6),
            "semantic_score": round(self.semantic_score, 6),
            "sources": list(self.sources),
        }


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]], k: int = 60, weights: Sequence[float] | None = None
) -> dict[str, float]:
    """Fuse ranked id lists into one score per id.

    ``k`` damps the influence of the top ranks so a single retriever's first
    hit cannot dominate. Classic RRF; see Cormack et al. 2009.
    """
    if weights is None:
        weights = [1.0] * len(rankings)
    fused: dict[str, float] = {}
    for ranking, weight in zip(rankings, weights):
        for position, doc_id in enumerate(ranking):
            fused[doc_id] = fused.get(doc_id, 0.0) + weight / (k + position + 1)
    return fused


class Bm25Retriever:
    """Okapi BM25 lexical retrieval."""

    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._chunks: list[dict] = []
        self._bm25 = None
        self._tokenized: list[list[str]] = []
        self._vocabulary: set[str] = set()

    def fit(self, chunks: Sequence[dict]) -> Bm25Retriever:
        self._chunks = list(chunks)
        self._tokenized = [tokenize(self._text_of(chunk)) for chunk in self._chunks]
        self._vocabulary = {term for tokens in self._tokenized for term in set(tokens)}
        # rank_bm25 raises on an empty corpus; an empty index must stay usable.
        self._bm25 = None
        if self._tokenized and any(self._tokenized):
            try:
                from rank_bm25 import BM25Okapi

                self._bm25 = BM25Okapi(self._tokenized, k1=self.k1, b=self.b)
            except Exception:
                # Degrade to substring scoring rather than lose lexical search.
                self._bm25 = None
        return self

    @staticmethod
    def _text_of(chunk: dict) -> str:
        return str(chunk.get("indexed_text") or chunk.get("content") or "")

    def expanded_tokens(self, query: str, *, min_ratio: float = 0.78) -> list[str]:
        """Query tokens plus cross-lingual, morphological and spelling fixes.

        Single source of truth for expansion so BM25 and the hybrid wrapper
        cannot disagree about what is being searched.
        """
        tokens = tokenize(query)
        if not tokens:
            return []
        # Cross-lingual first: it is the only layer that can turn a query whose
        # terms are absent from the corpus into one that has any.
        tokens = tokens + expand_bilingual(query)
        tokens = tokens + expand_query(tokens, self._vocabulary)
        return tokens + expand_query_fuzzy(tokens, self._vocabulary, min_ratio=min_ratio)

    def search(self, query: str, top_k: int = 5, expand: bool = True) -> list[ScoredChunk]:
        if not self._chunks:
            return []
        # Publish the vocabulary so query_is_coherent() can judge the query
        # against the actual corpus rather than a guess.
        set_vocabulary_snapshot(self._vocabulary)
        if not query_is_coherent(query):
            return []
        tokens = self.expanded_tokens(query) if expand else tokenize(query)
        if not tokens:
            return []

        if self._bm25 is not None:
            scores = np.asarray(self._bm25.get_scores(tokens), dtype=np.float64)
        else:
            scores = np.zeros(len(self._chunks))
            query_set = set(tokens)
            for i, doc_tokens in enumerate(self._tokenized):
                if not doc_tokens:
                    continue
                overlap = len(query_set & set(doc_tokens))
                if overlap:
                    scores[i] = overlap / len(query_set)

        ranked = np.argsort(-scores)[:top_k]
        results = []
        for position in ranked:
            if scores[position] <= 0:
                continue
            results.append(
                ScoredChunk(
                    chunk=self._chunks[position],
                    score=float(scores[position]),
                    lexical_score=float(scores[position]),
                    sources=[self.name],
                )
            )
        return results


class DenseRetriever:
    """Cosine similarity over dense chunk vectors."""

    name = "dense"

    def __init__(self, embedder: BaseEmbedder):
        self.embedder = embedder
        self._chunks: list[dict] = []
        self._vectors = np.zeros((0, 0))

    def fit(self, chunks: Sequence[dict], embedder: BaseEmbedder | None = None) -> DenseRetriever:
        if embedder is not None:
            self.embedder = embedder
        self._chunks = list(chunks)
        if not self._chunks:
            self._vectors = np.zeros((0, 0))
            return self
        corpus = [
            str(chunk.get("indexed_text") or chunk.get("content") or "") for chunk in self._chunks
        ]
        self.embedder.fit(corpus)
        self._vectors = np.asarray(self.embedder.encode(corpus), dtype=np.float64)
        return self

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        if not self._chunks or self._vectors.size == 0:
            return []
        query_vector = np.asarray(self.embedder.encode([query]), dtype=np.float64)
        if query_vector.size == 0 or query_vector.shape[1] != self._vectors.shape[1]:
            return []
        # Vectors are already L2-normalised, so the dot product is cosine.
        scores = (self._vectors @ query_vector[0]).ravel()
        order = np.argsort(-scores)[:top_k]
        results = []
        for position in order:
            if scores[position] <= 0:
                continue
            results.append(
                ScoredChunk(
                    chunk=self._chunks[position],
                    score=float(scores[position]),
                    semantic_score=float(scores[position]),
                    sources=[self.name],
                )
            )
        return results


class HybridRetriever:
    """BM25 + dense, fused with RRF and reranked by a score floor."""

    name = "hybrid"

    def __init__(
        self,
        embedder: BaseEmbedder | None = None,
        *,
        k1: float = 1.5,
        b: float = 0.75,
        rrf_k: int = 60,
        lexical_weight: float = 1.0,
        semantic_weight: float = 1.0,
        min_score: float = 0.0,
        max_per_document: int = 1,
        dedup_threshold: float = 0.85,
        fuzzy_min_ratio: float = 0.78,
    ):
        self.bm25 = Bm25Retriever(k1=k1, b=b)
        self.dense = DenseRetriever(embedder) if embedder is not None else None
        self.rrf_k = rrf_k
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight
        self.min_score = min_score
        self.max_per_document = max_per_document
        self.dedup_threshold = dedup_threshold
        self.fuzzy_min_ratio = fuzzy_min_ratio
        self._chunks: list[dict] = []
        self._by_id: dict[str, dict] = {}

    def fit(self, chunks: Sequence[dict]) -> HybridRetriever:
        self._chunks = list(chunks)
        self._by_id = {
            str(chunk.get("id", index)): chunk for index, chunk in enumerate(self._chunks)
        }
        self.bm25.fit(self._chunks)
        if self.dense is not None:
            self.dense.fit(self._chunks)
        return self

    @property
    def backend(self) -> str:
        """Name of the dense backend in use, if any."""
        return getattr(self.dense.embedder, "backend", "none") if self.dense else "disabled"

    def expand(self, query: str) -> list[str]:
        """Query tokens, plus morphological and spelling corrections.

        Delegates to the lexical retriever so callers and tests see exactly
        what BM25 will search.
        """
        return self.bm25.expanded_tokens(query, min_ratio=self.fuzzy_min_ratio)

    @staticmethod
    def _near_duplicate(candidate: dict, chosen: list[dict], threshold: float) -> bool:
        """True when ``candidate`` is close enough to an already-chosen chunk.

        Adjacent chunks of one document share their overlap window, so without
        this a single long document fills every slot in the result list.
        """
        text = str(candidate.get("content") or "")
        tokens = set(tokenize(text))
        if not tokens:
            return True
        for existing in chosen:
            other = set(tokenize(str(existing.get("content") or "")))
            if not other:
                return True
            intersection = len(tokens & other)
            union = len(tokens | other)
            if union and intersection / union >= threshold:
                return True
        return False

    def search(self, query: str, top_k: int = 5, **_: object) -> list[ScoredChunk]:
        """Return the best ``top_k`` chunks for ``query``, diverse across documents."""
        if not self._chunks:
            return []

        # Over-fetch so fusion has candidates from both retrievers.
        pool = max(top_k * 4, 20)
        lexical = self.bm25.search(query, top_k=pool)
        semantic = self.dense.search(query, top_k=pool) if self.dense else []

        if not lexical and not semantic:
            # No evidence found. Returning nothing is the honest answer; the
            # previous character-n-gram fallback invented matches instead.
            return []

        fused = reciprocal_rank_fusion(
            [
                [self._id_of(r.chunk) for r in lexical],
                [self._id_of(r.chunk) for r in semantic],
            ],
            k=self.rrf_k,
            weights=[self.lexical_weight, self.semantic_weight],
        )

        lex_scores = {self._id_of(r.chunk): r.lexical_score for r in lexical}
        sem_scores = {self._id_of(r.chunk): r.semantic_score for r in semantic}
        sources_by_id: dict[str, list[str]] = {}
        for result in lexical + semantic:
            sources_by_id.setdefault(self._id_of(result.chunk), []).extend(result.sources)

        ranked = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))
        out: list[ScoredChunk] = []
        chosen_chunks: list[dict] = []
        per_document: dict[str, int] = {}

        for chunk_id, score in ranked:
            if len(out) >= top_k:
                break
            if score < self.min_score:
                continue
            chunk = self._by_id[chunk_id]
            doc_id = str(chunk.get("doc_id", ""))
            if self.max_per_document and per_document.get(doc_id, 0) >= self.max_per_document:
                continue
            if self.dedup_threshold and self._near_duplicate(chunk, chosen_chunks, self.dedup_threshold):
                continue
            per_document[doc_id] = per_document.get(doc_id, 0) + 1
            chosen_chunks.append(chunk)
            out.append(
                ScoredChunk(
                    chunk=chunk,
                    score=score,
                    lexical_score=lex_scores.get(chunk_id, 0.0),
                    semantic_score=sem_scores.get(chunk_id, 0.0),
                    sources=sorted(set(sources_by_id.get(chunk_id, []))),
                )
            )
        return out

    @staticmethod
    def _id_of(chunk: dict) -> str:
        return str(chunk.get("id", ""))

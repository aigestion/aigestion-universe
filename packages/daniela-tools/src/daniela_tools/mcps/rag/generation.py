"""Answer composition from retrieved chunks.

There is no LLM wired into this project, so "generation" means building a
grounded, extractive answer: the caller gets the relevant passages plus the
citations needed to check them. If a model callable is supplied the context is
handed to it instead and its output is returned, which is the seam where a real
model would be plugged in.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from .retrieval import ScoredChunk
from .text import keywords

__all__ = ["Answer", "compose_answer", "build_context"]

# Answering a question from passages, without a model.
Extractor = Callable[[str, Sequence[dict]], str]


class Answer:
    """A grounded answer plus the evidence it was drawn from."""

    def __init__(self, text: str, sources: Sequence[dict], context: str, used_model: bool = False):
        self.text = text
        self.sources = list(sources)
        self.context = context
        self.used_model = used_model

    def to_dict(self) -> dict:
        return {
            "answer": self.text,
            "sources": self.sources,
            "context": self.context,
            "used_model": self.used_model,
        }

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"Answer(chars={len(self.text)}, sources={len(self.sources)}, model={self.used_model})"


def build_context(results: Sequence[ScoredChunk], *, max_chars: int = 4000) -> str:
    """Render retrieved chunks into a numbered context block.

    Chunks are truncated at a sentence boundary where possible so a citation
    never points at half a sentence.
    """
    if not results:
        return ""
    blocks: list[str] = []
    used = 0
    for number, result in enumerate(results, start=1):
        chunk = result.chunk
        title = str(chunk.get("title") or chunk.get("doc_id") or "document")
        body = str(chunk.get("content") or "")
        remaining = max_chars - used
        if remaining <= 0:
            break
        excerpt = _clip(body, remaining)
        if not excerpt:
            continue
        block = f"[{number}] {title}\n{excerpt}"
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def _clip(text: str, limit: int) -> str:
    """Cut ``text`` to ``limit`` characters, preferring a sentence boundary."""
    text = text.strip()
    if len(text) <= limit:
        return text
    window = text[:limit]
    for boundary in (". ", "? ", "! ", "\n"):
        position = window.rfind(boundary)
        if position > limit * 0.6:
            return window[: position + 1].strip()
    return window.rstrip() + "..."


def _extract(query: str, sources: Sequence[dict], max_sentences: int = 6) -> str:
    """Pick the sentences that overlap the query most.

    Ranks candidate sentences by query-token overlap, then restores reading
    order so the extract still reads naturally.
    """
    if not sources:
        return ""

    from .text import tokenize

    query_tokens = set(tokenize(query))
    candidates: list[tuple[int, int, float, str]] = []
    for source_index, source in enumerate(sources):
        body = str(source.get("content") or "")
        title = str(source.get("title") or "")
        for position, sentence in enumerate(_sentences(body)):
            # The title is part of every chunk's indexed text, so a sentence
            # matching the title counts for more than one matching the body.
            title_tokens = set(tokenize(title))
            sentence_tokens = set(tokenize(sentence)) | title_tokens | title_tokens
            overlap = len(query_tokens & sentence_tokens)
            if overlap == 0:
                continue
            score = overlap / max(len(query_tokens), 1)
            candidates.append((source_index, position, score, sentence))

    if not candidates:
        first = sources[0]
        return str(first.get("content") or "")[:400].strip()

    candidates.sort(key=lambda item: -item[2])
    chosen = candidates[:max_sentences]
    # Reading order, grouped by source so citations stay coherent.
    chosen.sort(key=lambda item: (item[0], item[1]))

    lines: list[str] = []
    current_source = None
    for source_index, _position, _score, sentence in chosen:
        title = str(sources[source_index].get("title") or f"source {source_index + 1}")
        if source_index != current_source:
            lines.append(f"\n{title}:")
            current_source = source_index
        lines.append(f"  - {sentence}")
    return "\n".join(lines).strip()


def _sentences(text: str) -> list[str]:
    """Split into sentences without losing the terminator."""
    parts: list[str] = []
    buffer = ""
    for chunk in text.replace("\n", " \n").split(". "):
        piece = (buffer + chunk).strip()
        if not piece:
            continue
        if not piece.endswith((".", "!", "?")):
            buffer = piece + ". "
            continue
        parts.append(piece)
        buffer = ""
    if buffer.strip():
        parts.append(buffer.strip())
    return [p for p in parts if len(p) > 2]


def compose_answer(
    query: str,
    results: Sequence[ScoredChunk],
    *,
    generator: Extractor | None = None,
    max_context_chars: int = 4000,
    max_sources: int = 5,
) -> Answer:
    """Turn retrieved chunks into an answer.

    When ``generator`` is given it receives ``(query, context)`` and its return
    value becomes the answer; otherwise an extractive summary is produced.
    """
    top = list(results)[:max_sources]
    sources = [result.to_dict() for result in top]
    context = build_context(top, max_chars=max_context_chars)

    if generator is not None and context:
        try:
            text = generator(query, sources)
            if text and text.strip():
                return Answer(text.strip(), sources, context, used_model=True)
        except Exception:
            # A failing generator must not lose the retrieved evidence.
            pass

    if not top:
        empty = Answer(
            f"No se encontró contexto relevante para: {query}" if query else "No query supplied.",
            [],
            "",
        )
        return empty

    terms = ", ".join(keywords(query, limit=6))
    body = _extract(query, sources)
    header = f"Contexto recuperado ({len(top)} fragmento(s)) para «{query}»"
    if terms:
        header += f"\nTérminos clave: {terms}"
    return Answer(f"{header}\n{body}" if body else header, sources, context)


def format_sources(results: Sequence[ScoredChunk]) -> str:
    """Render a citation list for the given results."""
    if not results:
        return "Sin fuentes."
    lines = []
    for number, result in enumerate(results, start=1):
        chunk = result.chunk
        title = str(chunk.get("title") or chunk.get("doc_id") or "document")
        source = str(chunk.get("source") or "")
        suffix = f" — {source}" if source else ""
        lines.append(f"[{number}] {title}{suffix} (score {result.score:.4f})")
    return "\n".join(lines)

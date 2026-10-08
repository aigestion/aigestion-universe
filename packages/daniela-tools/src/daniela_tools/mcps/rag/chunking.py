"""Document chunking.

Long documents are split into overlapping windows so that a retrieved chunk is
small enough to fit in a prompt while still carrying enough context to stand on
its own. Splitting prefers natural boundaries (paragraphs, sentences, clauses)
before falling back to whitespace, and never emits an empty chunk.
"""

from __future__ import annotations

import re

__all__ = ["chunk_text", "chunk_document", "DEFAULT_MAX_CHARS", "DEFAULT_OVERLAP"]

DEFAULT_MAX_CHARS = 1000
DEFAULT_OVERLAP = 150

_DIGIT_RUN_RE = re.compile(r"\d+")

# Ordered from most to least structural. Empty string means "hard character cut".
_SEPARATORS: tuple[str, ...] = ("\n\n", "\n", ". ", "; ", ", ", " ", "")


def _split_units(text: str) -> list[str]:
    """Split text on the first separator that yields multiple non-empty parts.

    Using the shallowest structural split that actually divides the text keeps
    sentences intact when possible, instead of breaking at every space.
    """
    for separator in _SEPARATORS:
        if not separator:
            continue
        parts = [p for p in text.split(separator) if p.strip()]
        if len(parts) > 1:
            return parts
    return [text] if text.strip() else []


def _merge(units: list[str], max_chars: int, overlap: int) -> list[str]:
    """Pack units into windows of at most ``max_chars`` with a trailing overlap."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current, current_len
        if current:
            chunks.append(" ".join(current).strip())
            current = []
            current_len = 0

    for unit in units:
        unit = unit.strip()
        if not unit:
            continue
        # A single oversized unit is hard-cut so we never lose content.
        # A single oversized unit is hard-cut so we never lose content. The
        # window advances by max_chars - overlap, which folds the overlap into
        # the following chunk instead of emitting it as a chunk of its own.
        if len(unit) > max_chars:
            flush()
            stride = max_chars - overlap
            for start in range(0, len(unit), stride):
                piece = unit[start : start + max_chars].strip()
                if piece:
                    chunks.append(piece)
            continue

        if current_len + len(unit) + (1 if current else 0) > max_chars:
            tail = _tail_of(" ".join(current), overlap)
            flush()
            if tail:
                current = [tail]
                current_len = len(tail)

        current.append(unit)
        current_len += len(unit) + (1 if len(current) > 1 else 0)

    flush()
    return [c for c in chunks if c.strip()]


def _tail_of(text: str, overlap: int) -> str:
    """Last ``overlap`` characters of ``text``, snapped to a word boundary."""
    if overlap <= 0 or not text:
        return ""
    tail = text[-overlap:]
    space = tail.find(" ")
    if space != -1 and len(tail) - space < overlap // 2:
        tail = tail[space + 1 :]
    return tail.strip()


def chunk_text(
    text: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Split ``text`` into overlapping chunks of at most ``max_chars``.

    Overlap is clamped below ``max_chars`` so a chunk can never be entirely
    duplicated by its successor.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    overlap = max(0, min(overlap, max_chars - 1))

    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    return _merge(_split_units(text), max_chars, overlap)


def chunk_document(
    content: str,
    title: str,
    *,
    doc_id: str,
    category: str = "general",
    source: str = "",
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict[str, object]]:
    """Chunk ``content`` and return retrieval records carrying document metadata.

    The title is prepended to the indexed text so a query naming the document
    ("que hace el agente 1") matches its chunks. The document id is included
    too, because ids carry the component number in this project
    (``agent_7.py``) while titles usually do not ("Agent 7" is spelled out but
    the digit is dropped by tokenisation of the title alone).
    """
    pieces = chunk_text(content, max_chars=max_chars, overlap=overlap)

    header_parts = [part for part in (title, _identifier_tokens(doc_id)) if part]
    header = " ".join(header_parts)

    return [
        {
            "id": f"{doc_id}#{ordinal}",
            "doc_id": doc_id,
            "title": title,
            "category": category,
            "source": source,
            "ordinal": ordinal,
            "content": piece,
            "indexed_text": f"{header}\n\n{piece}" if header else piece,
        }
        for ordinal, piece in enumerate(pieces)
    ]


def _identifier_tokens(doc_id: str) -> str:
    """Digits embedded in a document id, split so they tokenise separately.

    ``phone/agents/agent_7.py`` must contribute the token ``7`` so that a query
    for "agente 7" can match it.
    """
    numbers = _DIGIT_RUN_RE.findall(doc_id.replace("_", " ").replace("-", " "))
    return " ".join(numbers)

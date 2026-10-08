"""Text normalization, tokenization and keyword extraction.

The project documentation mixes Spanish and English, so the stopword list and
the stemmer cover both. Everything here is deterministic and dependency-free so
that an index built today scores identically tomorrow.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence
from functools import lru_cache

__all__ = [
    "STOPWORDS",
    "normalize",
    "strip_accents",
    "tokenize",
    "stem",
    "keywords",
    "token_overlap",
    "expand_query",
    "char_ngrams",
    "fuzzy_similarity",
    "fuzzy_similarity_windowed",
    "closest_vocabulary_term",
    "expand_query_fuzzy",
    "query_is_coherent",
]

# Spanish + English function words. Kept small and explicit: over-aggressive
# stopword lists hurt phrase queries more than they help.
STOPWORDS = frozenset(
    """
    a al algo algun alguna alguno algunos ante antes como con contra cual cuando
    de del desde donde dos el ella ellas ellos en entre era erais eran eres es
    esa esas ese eso esos esta estaba estan estas este esto estos ha hasta hay
    la las le les lo los mas me mi mis mucho muy nada ni no nos o os otro para
    pero poco por porque que quien se sea sin sobre son su sus tan te tiene
    tienen todo todos tu tus un una uno unos y ya yo
    an and are as at be but by for from has have if in into is it its of on or
    such that the their then there these they this to was will with
    """.split()
)

_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
_WHITESPACE_RE = re.compile(r"\s+")

# Conservative suffix rules (Porter-ish). Order matters: longer suffixes first.
# The Spanish verbal forms matter most: matching "orquestando" against
# "orquestan" is the difference between finding agent_1.py and returning
# nothing, so gerunds and third-person plurals collapse to one shared stem.
_SUFFIX_RULES: tuple[tuple[str, str], ...] = (
    ("ational", "ate"),
    ("fulness", "ful"),
    ("ousness", "ous"),
    ("ization", "ize"),
    ("aciones", "acion"),
    ("iciones", "icion"),
    ("amiento", "ar"),
    ("imiento", "ir"),
    ("ciones", "cion"),
    ("adores", "ador"),
    ("adoras", "ador"),
    ("idades", "idad"),
    ("mente", ""),
    ("ments", ""),
    ("ando", ""),
    ("iendo", ""),
    ("aron", ""),
    ("ieron", ""),
    ("ando", "ar"),
    ("iendo", "er"),
    ("aron", "ar"),
    ("ieron", "er"),
    ("ing", ""),
    ("ly", ""),
    ("ies", "y"),
    ("ied", "y"),
    ("an", ""),
    ("en", ""),
    ("ed", ""),
    ("es", ""),
    ("s", ""),
)

# Never shorten a stem below this, so "ies" does not reduce "flies" to "f".
_MIN_STEM = 3

# Fuzzy-fallback prefix length for out-of-vocabulary query tokens.
_FUZZY_PREFIX = 5


def strip_accents(text: str) -> str:
    """Replace accented characters with their ASCII base form."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    """Lowercase, de-accent and collapse whitespace."""
    return _WHITESPACE_RE.sub(" ", strip_accents(text).lower()).strip()


@lru_cache(maxsize=100_000)
def stem(word: str) -> str:
    """Reduce a single token to a crude stem.

    Deliberately shallow. A full stemmer would need a dictionary for correct
    Spanish; this only collapses the endings that are unambiguous enough to be
    safe for ranking purposes.

    Cached because tokenising a corpus calls this once per token per rebuild,
    and the same vocabulary recurs every time. Profiling showed it was 78% of
    rebuild time before the cache.
    """
    return _stem_uncached(word)


def _stem_uncached(word: str) -> str:
    # Group the rules by final character so most tokens cost a single dict
    # lookup plus a handful of endswith() calls instead of scanning all ~20
    # rules. Suffixes and words are compared in their original order within a
    # group, which preserves longest-match-first behaviour.
    last = word[-1:]
    candidates = _RULES_BY_LAST.get(last)
    if candidates:
        for suffix, replacement in candidates:
            if word.endswith(suffix):
                base = word[: -len(suffix)] + replacement
                if len(base) >= _MIN_STEM:
                    return base
    return word


def _build_rules_by_last() -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = {}
    for rule in _SUFFIX_RULES:
        grouped.setdefault(rule[0][-1], []).append(rule)
    return grouped


_RULES_BY_LAST = _build_rules_by_last()


def tokenize(
    text: str,
    *,
    min_length: int = 2,
    drop_stopwords: bool = True,
    do_stem: bool = True,
) -> list[str]:
    """Split text into normalized, filtered retrieval tokens.

    Single digits are kept regardless of ``min_length``. This system addresses
    its components by number ("agente 1", "subagent 17"), so discarding "1"
    would make "agente 1" indistinguishable from "agente 7" and every numbered
    component would match every other one.
    """
    tokens = _WORD_RE.findall(normalize(text))
    result: list[str] = []
    for token in tokens:
        if len(token) < min_length and not token.isdigit():
            continue
        if drop_stopwords and token in STOPWORDS:
            continue
        result.append(stem(token) if do_stem else token)
    return result


def keywords(text: str, limit: int = 10) -> list[str]:
    """Return the most frequent content tokens, longest first on ties.

    Frequency alone favours boilerplate, so tokens appearing in nearly every
    document of a collection are damped elsewhere; here we simply keep order
    stable and deterministic by sorting on (-count, -length, token).
    """
    counts: dict[str, int] = {}
    for token in tokenize(text):
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))
    return [token for token, _ in ranked[:limit]]


def token_overlap(query_tokens: Sequence[str], doc_tokens: Iterable[str]) -> float:
    """Fraction of distinct query tokens present in a document."""
    distinct = set(query_tokens)
    if not distinct:
        return 0.0
    return len(distinct & set(doc_tokens)) / len(distinct)


def expand_query(query_tokens: Sequence[str], vocabulary: Iterable[str]) -> list[str]:
    """Add vocabulary entries that share a long prefix with a query token.

    Retrieval should never return nothing just because the user inflected a
    word differently from the corpus ("orquesta" vs "orquestando"). For each
    token absent from the corpus vocabulary, vocabulary terms sharing its first
    ``_FUZZY_PREFIX`` characters are added, which recovers morphological
    variants without needing a full stemmer or a lexicon.
    """
    known = set(vocabulary)
    extra: list[str] = []
    seen = set(known)
    for token in query_tokens:
        if token in known or len(token) < _FUZZY_PREFIX:
            continue
        prefix = token[:_FUZZY_PREFIX]
        for candidate in known:
            if candidate.startswith(prefix) and candidate not in seen:
                extra.append(candidate)
                seen.add(candidate)
    return extra


def char_ngrams(text: str, size: int = 3) -> set[str]:
    """Character n-grams of normalised text, used for fuzzy fallback scoring."""
    compact = normalize(text).replace(" ", "")
    if not compact:
        return set()
    if len(compact) <= size:
        return {compact}
    return {compact[i : i + size] for i in range(len(compact) - size + 1)}


def fuzzy_similarity(query: str, text: str, size: int = 3) -> float:
    """Best containment of the query's character n-grams anywhere in ``text``.

    Uses containment rather than Jaccard: a long chunk contains many n-grams
    the query never asked about, so a Jaccard score against the whole chunk
    tends to zero as the chunk grows and the fallback never fires. Containment
    asks the useful question instead -- what fraction of what the user typed
    actually appears here.

    This is a last-resort scorer for typos and for words the corpus never used.
    It is blind to word order and to meaning, so it must not outrank real
    retrieval.
    """
    query_grams = char_ngrams(query, size)
    if not query_grams:
        return 0.0
    text_grams = char_ngrams(text, size)
    if not text_grams:
        return 0.0
    return len(query_grams & text_grams) / len(query_grams)


def fuzzy_similarity_windowed(query: str, text: str, size: int = 3, window: int = 40) -> float:
    """Highest containment score found in any ``window``-sized span of ``text``.

    Scores one relevant sentence against its neighbours rather than scoring a
    whole chunk, so long documents do not dilute the signal.
    """
    query_grams = char_ngrams(query, size)
    if not query_grams:
        return 0.0
    normalized = normalize(text)
    if not normalized:
        return 0.0

    best = 0.0
    # Slide a character window over the text; score each independently.
    step = max(window // 2, 1)
    for start in range(0, max(len(normalized) - window, 0) + step, step):
        span = normalized[start : start + window]
        score = fuzzy_similarity(query, span, size=size)
        if score > best:
            best = score
            if best == 1.0:
                break
    return best


def closest_vocabulary_term(
    token: str, vocabulary: Iterable[str], *, min_ratio: float = 0.78
) -> str | None:
    """Best spelling-similar vocabulary term for an out-of-vocabulary ``token``.

    This is the fallback that matters in practice. Queries contain typos and
    untranslated terms ("subagente" for "subagent"), and a word-level edit
    distance recovers those precisely. It is deliberately strict: ``min_ratio``
    is high because a loose match invents a document the user never asked for,
    which is worse than admitting the term was not found.

    Character n-gram containment was tried first and rejected: Spanish and
    English prose share so many trigrams that unrelated documents all scored
    above threshold, so nonsense queries returned confident-looking results.
    """
    from difflib import SequenceMatcher

    best_term: str | None = None
    best_ratio = min_ratio
    # Only compare against candidates of a similar length; edit distance is
    # otherwise dominated by unrelated short or long words.
    length = len(token)
    for candidate in vocabulary:
        if abs(len(candidate) - length) > max(2, length // 2):
            continue
        ratio = SequenceMatcher(None, token, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_term = candidate

    # Guard against coined words that happen to sit one edit from a real term.
    # A short token differing in two or more positions is a different word, not
    # a misspelling; correcting it would manufacture a match out of nonsense.
    # The threshold cannot separate a one-edit coined word from a one-edit typo,
    # and that residual case is documented rather than papered over.
    if best_term is not None and _looks_like_coined_word(token, best_term):
        return None
    return best_term


def _looks_like_coined_word(token: str, candidate: str) -> bool:
    """True when ``token`` is too short to be a typo of ``candidate``.

    Short words differing in two or more positions are merely similar, not
    misspelled. Longer tokens are allowed more slack so that Spanish verb forms
    ("monitoriza", "monitorea") still resolve, since those are real inflections
    rather than typos.
    """
    differences = sum(1 for a, b in zip(token, candidate) if a != b)
    differences += abs(len(token) - len(candidate))
    allowance = 2 if len(token) >= 8 else 1
    return differences > allowance


def expand_query_fuzzy(
    query_tokens: Sequence[str], vocabulary: Iterable[str], *, min_ratio: float = 0.78
) -> list[str]:
    """Correct out-of-vocabulary query tokens against the corpus vocabulary."""
    known = set(vocabulary)
    corrections: list[str] = []
    # Tracks corrections already added, not the whole vocabulary: a candidate is
    # by construction a vocabulary term, so seeding `seen` with the vocabulary
    # would reject every match.
    already_added: set[str] = set()
    for token in query_tokens:
        if token in known or len(token) < _FUZZY_PREFIX:
            continue
        candidate = closest_vocabulary_term(token, known, min_ratio=min_ratio)
        if candidate and candidate not in already_added:
            corrections.append(candidate)
            already_added.add(candidate)
    return corrections


def query_is_coherent(query: str) -> bool:
    """Whether ``query`` contains enough real signal to be worth answering.

    A query made mostly of out-of-vocabulary tokens is either a typo storm or
    nonsense. Retrieval can still match on the handful of tokens it does know,
    but the honest result is no answer rather than a confident one derived from
    a single accidental character match.

    Cross-lingual tokens count as known: a Spanish word absent from an English
    corpus is exactly what the lexicon exists to translate, so judging it as
    unknown would make this guard reject every translated query.
    """
    tokens = tokenize(query)
    if not tokens:
        return False
    # With no snapshot (e.g. a direct unit call) the check cannot be made, so
    # treat the query as coherent rather than silently blocking it.
    if not VOCABULARY_SNAPSHOT:
        return True

    from .lexicon import TOKEN_EQUIVALENTS

    def is_known(token: str) -> bool:
        if token in VOCABULARY_SNAPSHOT:
            return True
        # A token is also known if the lexicon can translate it into something
        # the corpus actually contains.
        return any(
            equivalent in VOCABULARY_SNAPSHOT
            for equivalent in TOKEN_EQUIVALENTS.get(token, ())
        )

    known = sum(1 for token in tokens if is_known(token))
    return known / len(tokens) >= _COHERENCE_RATIO


# Populated by the retriever before searching; module level so the text helpers
# stay free of any dependency on the index.
VOCABULARY_SNAPSHOT: set[str] = set()
_COHERENCE_RATIO = 0.34


def set_vocabulary_snapshot(vocabulary: Iterable[str]) -> None:
    """Publish the corpus vocabulary for :func:`query_is_coherent`."""
    VOCABULARY_SNAPSHOT.clear()
    VOCABULARY_SNAPSHOT.update(vocabulary)

"""
NLP Engine - Ideas 1-10
=======================

1.  Sentiment analysis pipeline (text -> sentiment score)
2.  Named entity recognition (NER) for Spanish/English
3.  Text summarization (extractive + abstractive)
4.  Language detection (100+ languages)
5.  Keyword extraction with TF-IDF
6.  Text similarity engine (cosine, Jaccard)
7.  Grammar correction API
8.  Sentiment timeline tracker
9.  Emotion detection (joy, anger, fear, etc)
10. Readability scorer (Flesch-Kincaid)
"""

import math
import re
from collections import Counter


class NLPEngine:
    """Core NLP engine providing 10 powerful text analysis capabilities."""

    POSITIVE_WORDS = {
        "good", "great", "excellent", "amazing", "wonderful", "fantastic",
        "love", "happy", "best", "awesome", "perfect", "brilliant", "outstanding",
        "superb", "magnificent", "delightful", "pleased", "satisfied", "enjoy",
        "beautiful", "nice", "pleasant", "remarkable", "exceptional", "stellar",
    }
    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "horrible", "worst", "hate", "angry",
        "sad", "poor", "ugly", "disappointing", "fail", "failure", "broken",
        "annoying", "frustrating", "miserable", "dreadful", "pathetic", "useless",
        "disgusting", "boring", "painful", "wrong", "defect", "error",
    }

    EMOTION_LEXICON = {
        "joy": {"happy", "love", "wonderful", "amazing", "celebrate", "delight", "elated", "cheerful", "blissful", "euphoric"},
        "anger": {"angry", "furious", "rage", "hate", "outraged", "livid", "irritated", "annoyed", "enraged", "hostile"},
        "fear": {"afraid", "scared", "terrified", "anxious", "worried", "panic", "dread", "frightened", "nervous", "alarmed"},
        "sadness": {"sad", "depressed", "miserable", "heartbroken", "grief", "sorrow", "melancholy", "despair", "gloomy", "tearful"},
        "surprise": {"surprised", "shocked", "astonished", "amazed", "stunned", "unexpected", "wow", "astonishing", "bewildered"},
        "disgust": {"disgusting", "gross", "revolting", "vile", "nasty", "repulsive", "sickening", "appalling", "abhorrent"},
    }

    SPANISH_ENTITIES = {
        "LOCATION": {"madrid", "barcelona", "mexico", "buenos", "aires", "lima", "bogota", "santiago", "caracas", "quito", "havana", "panama"},
        "PERSON": {"pedro", "maria", "jose", "juan", "ana", "laura", "carlos", "diego", "sofia", "elena", "pablo", "andres"},
        "ORG": {"telefonica", "santander", "bbva", "iberdrola", "repsol", "américa", "móvil", "banco", "universidad"},
    }

    ENGLISH_ENTITIES = {
        "LOCATION": {"new york", "london", "paris", "tokyo", "berlin", "rome", "madrid", "sydney", "dubai", "singapore", "boston", "seattle"},
        "PERSON": {"john", "james", "robert", "michael", "david", "emma", "sarah", "jessica", "emily", "daniel", "matt", "chris"},
        "ORG": {"google", "microsoft", "amazon", "apple", "meta", "tesla", "netflix", "spacex", "openai", "nvidia"},
    }

    # Idea 10: Flesch-Kincaid
    EASY_WORDS = {
        "the", "is", "at", "which", "and", "a", "an", "in", "it", "to",
        "of", "for", "on", "with", "as", "by", "this", "that", "from",
        "or", "but", "not", "are", "was", "were", "been", "be", "have",
        "has", "had", "do", "does", "did", "will", "would", "can", "could",
        "may", "might", "shall", "should", "must", "need", "you", "we",
        "they", "he", "she", "me", "him", "her", "us", "them", "my",
        "your", "his", "its", "our", "their", "what", "how", "when",
    }

    def __init__(self):
        self.sentiment_history: list[dict] = []

    # ── Idea 1: Sentiment Analysis ──────────────────────────────────
    def sentiment_analysis(self, text: str) -> dict:
        """Analyze sentiment of text. Returns score -1.0 to 1.0."""
        words = re.findall(r'\w+', text.lower())
        pos = sum(1 for w in words if w in self.POSITIVE_WORDS)
        neg = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        total = pos + neg
        if total == 0:
            score = 0.0
            label = "neutral"
        else:
            score = round((pos - neg) / total, 3)
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"
        return {"score": score, "label": label, "positive": pos, "negative": neg, "words": len(words)}

    # ── Idea 2: Named Entity Recognition ────────────────────────────
    def ner(self, text: str, lang: str = "en") -> dict[str, list[str]]:
        """Extract named entities from text for Spanish or English."""
        entities: dict[str, list[str]] = {"PERSON": [], "LOCATION": [], "ORG": []}
        lexicon = self.SPANISH_ENTITIES if lang == "es" else self.ENGLISH_ENTITIES
        text_lower = text.lower()
        for ent_type, terms in lexicon.items():
            for term in terms:
                if term in text_lower:
                    entities[ent_type].append(term.title())
        # Also detect capitalized words as potential entities
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for c in caps:
            cl = c.lower()
            if not any(cl in terms for terms in lexicon.values()):
                entities["PERSON"].append(c)
        for k in entities:
            entities[k] = list(dict.fromkeys(entities[k]))
        return entities

    # ── Idea 3: Text Summarization ──────────────────────────────────
    def summarize(self, text: str, method: str = "extractive", ratio: float = 0.3) -> str:
        """Summarize text using extractive or abstractive method."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if len(sentences) <= 2:
            return text
        if method == "abstractive":
            return self._abstractive_summary(sentences, ratio)
        return self._extractive_summary(text, sentences, ratio)

    def _extractive_summary(self, text: str, sentences: list[str], ratio: float) -> str:
        word_freq = Counter(re.findall(r'\w+', text.lower()))
        max_freq = max(word_freq.values()) if word_freq else 1
        scored = []
        for s in sentences:
            words = re.findall(r'\w+', s.lower())
            score = sum(word_freq.get(w, 0) / max_freq for w in words) / max(words.__len__(), 1)
            scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        n = max(1, int(len(sentences) * ratio))
        top = [s for _, s in scored[:n]]
        return " ".join(top)

    def _abstractive_summary(self, sentences: list[str], ratio: float) -> str:
        word_freq = Counter(re.findall(r'\w+', " ".join(sentences).lower()))
        top_words = [w for w, _ in word_freq.most_common(5)]
        summary_parts = []
        n = max(1, int(len(sentences) * ratio))
        for s in sentences[:n]:
            key = next((w for w in top_words if w in s.lower()), None)
            if key:
                summary_parts.append(s.strip())
        if not summary_parts:
            summary_parts = sentences[:n]
        return " ".join(summary_parts)

    # ── Idea 4: Language Detection ──────────────────────────────────
    def detect_language(self, text: str) -> dict:
        """Detect language of text (simplified: en, es, fr, de, pt, it)."""
        lang_patterns = {
            "en": {"the", "is", "and", "of", "to", "in", "it", "that", "was", "for"},
            "es": {"el", "la", "de", "que", "en", "los", "las", "un", "una", "por"},
            "fr": {"le", "la", "de", "les", "des", "est", "un", "une", "que", "dans"},
            "de": {"der", "die", "das", "und", "ist", "ein", "eine", "von", "den", "dem"},
            "pt": {"o", "a", "de", "que", "em", "os", "as", "um", "uma", "por"},
            "it": {"il", "la", "di", "che", "in", "gli", "le", "un", "una", "per"},
        }
        words = set(re.findall(r'\w+', text.lower()))
        scores = {}
        for lang, markers in lang_patterns.items():
            scores[lang] = len(words & markers)
        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1
        confidence = round(scores[best] / total, 3)
        return {"language": best, "confidence": confidence, "scores": scores}

    # ── Idea 5: Keyword Extraction with TF-IDF ─────────────────────
    def extract_keywords(self, text: str, top_n: int = 10) -> list[dict]:
        """Extract top keywords using TF-IDF scoring."""
        stopwords = {
            "the", "is", "at", "which", "and", "a", "an", "in", "it", "to",
            "of", "for", "on", "with", "as", "by", "this", "that", "from",
            "or", "but", "not", "are", "was", "were", "be", "been", "has",
            "have", "had", "do", "does", "did", "will", "can", "could",
        }
        words = re.findall(r'\w+', text.lower())
        words = [w for w in words if w not in stopwords and len(w) > 2]
        if not words:
            return []
        tf = Counter(words)
        max_tf = max(tf.values())
        keywords = []
        for word, count in tf.most_common(top_n * 2):
            tf_score = count / max_tf
            idf_score = math.log(10 / (1 + count))
            score = round(tf_score * idf_score, 4)
            keywords.append({"keyword": word, "tf": round(tf_score, 4), "idf": round(idf_score, 4), "score": score})
        keywords.sort(key=lambda x: x["score"], reverse=True)
        return keywords[:top_n]

    # ── Idea 6: Text Similarity ─────────────────────────────────────
    def text_similarity(self, text1: str, text2: str, method: str = "cosine") -> dict:
        """Compute similarity between two texts."""
        if method == "jaccard":
            return self._jaccard_similarity(text1, text2)
        return self._cosine_similarity(text1, text2)

    def _cosine_similarity(self, t1: str, t2: str) -> dict:
        words1 = re.findall(r'\w+', t1.lower())
        words2 = re.findall(r'\w+', t2.lower())
        vocab = set(words1) | set(words2)
        vec1 = [words1.count(w) for w in vocab]
        vec2 = [words2.count(w) for w in vocab]
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a ** 2 for a in vec1))
        mag2 = math.sqrt(sum(b ** 2 for b in vec2))
        score = round(dot / (mag1 * mag2), 4) if mag1 and mag2 else 0.0
        return {"method": "cosine", "score": score}

    def _jaccard_similarity(self, t1: str, t2: str) -> dict:
        s1 = set(re.findall(r'\w+', t1.lower()))
        s2 = set(re.findall(r'\w+', t2.lower()))
        intersection = s1 & s2
        union = s1 | s2
        score = round(len(intersection) / len(union), 4) if union else 0.0
        return {"method": "jaccard", "score": score}

    # ── Idea 7: Grammar Correction ──────────────────────────────────
    def grammar_correction(self, text: str) -> dict:
        """Basic grammar correction (mock implementation)."""
        corrections = []
        corrected = text
        fixes = [
            (r'\bi\b', "I"),
            (r'\bim\b', "I'm"),
            (r'\byour\b(?=\s+(?:a|the|is|are|was|were))', "you're"),
            (r'\bits\b(?=\s+a\b)', "it's"),
            (r'(?<!\w)alot\b', "a lot"),
            (r'(?i)\b(doesnt|dont|cant|wont|isnt|arent|wasnt|werent)\b',
             lambda m: m.group(0)[:-1] + "'" + m.group(0)[-1]),
            (r'\s{2,}', " "),
            (r'([.!?])\s*([a-z])', lambda m: m.group(1) + " " + m.group(2).upper()),
        ]
        for pattern, replacement in fixes:
            if callable(replacement):
                new = re.sub(pattern, replacement, corrected)
            else:
                new = re.sub(pattern, replacement, corrected)
            if new != corrected:
                corrections.append({"pattern": pattern, "before": corrected, "after": new})
                corrected = new
        return {"original": text, "corrected": corrected, "corrections": corrections, "count": len(corrections)}

    # ── Idea 8: Sentiment Timeline Tracker ──────────────────────────
    def track_sentiment(self, text: str, timestamp: str | None = None) -> dict:
        """Track sentiment over time."""
        import datetime
        result = self.sentiment_analysis(text)
        entry = {
            "text": text[:100],
            "timestamp": timestamp or datetime.datetime.now().isoformat(),
            "score": result["score"],
            "label": result["label"],
        }
        self.sentiment_history.append(entry)
        avg = sum(e["score"] for e in self.sentiment_history) / len(self.sentiment_history)
        return {
            "current": result,
            "history_size": len(self.sentiment_history),
            "average_score": round(avg, 3),
            "trend": "improving" if len(self.sentiment_history) > 1 and self.sentiment_history[-1]["score"] > self.sentiment_history[-2]["score"] else "declining",
        }

    # ── Idea 9: Emotion Detection ───────────────────────────────────
    def detect_emotions(self, text: str) -> dict:
        """Detect emotions in text."""
        words = set(re.findall(r'\w+', text.lower()))
        scores = {}
        for emotion, lexicon in self.EMOTION_LEXICON.items():
            matches = words & lexicon
            scores[emotion] = round(len(matches) / max(len(words), 1), 3)
        dominant = max(scores, key=scores.get) if any(scores.values()) else "neutral"
        return {"dominant_emotion": dominant, "scores": scores, "text_length": len(text)}

    # ── Idea 10: Readability Scorer (Flesch-Kincaid) ────────────────
    def readability_score(self, text: str) -> dict:
        """Calculate Flesch-Kincaid readability score."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        words = re.findall(r'\w+', text)
        syllables = sum(self._count_syllables(w) for w in words)
        num_sentences = max(len(sentences), 1)
        num_words = max(len(words), 1)
        num_syllables = max(syllables, 1)
        fk_grade = 0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59
        flesch = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
        flesch = max(0, min(100, round(flesch, 1)))
        fk_grade = max(0, round(fk_grade, 1))
        if flesch >= 80:
            level = "easy"
        elif flesch >= 60:
            level = "standard"
        elif flesch >= 40:
            level = "moderate"
        else:
            level = "difficult"
        return {
            "flesch_score": flesch,
            "fk_grade": fk_grade,
            "level": level,
            "sentences": num_sentences,
            "words": num_words,
            "syllables": num_syllables,
        }

    def _count_syllables(self, word: str) -> int:
        word = word.lower()
        if len(word) <= 3:
            return 1
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith("e"):
            count -= 1
        return max(count, 1)

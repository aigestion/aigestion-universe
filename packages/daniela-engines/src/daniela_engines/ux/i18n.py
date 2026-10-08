"""Internationalization: 41-50."""

import re


class MultiLanguageSupport:
    """41. Multi-language support (i18n)."""

    def __init__(self, default_locale: str = "en"):
        self._default = default_locale
        self._translations: dict[str, dict[str, str]] = {}
        self._fallbacks: dict[str, str] = {}

    def add_translation(self, locale: str, key: str, value: str):
        if locale not in self._translations:
            self._translations[locale] = {}
        self._translations[locale][key] = value

    def add_translations(self, locale: str, translations: dict[str, str]):
        if locale not in self._translations:
            self._translations[locale] = {}
        self._translations[locale].update(translations)

    def translate(self, key: str, locale: str | None = None) -> str:
        loc = locale or self._default
        if loc in self._translations and key in self._translations[loc]:
            return self._translations[loc][key]
        fb = self._fallbacks.get(loc, self._default)
        if fb in self._translations and key in self._translations[fb]:
            return self._translations[fb][key]
        return key

    def t(self, key: str, locale: str | None = None) -> str:
        return self.translate(key, locale)

    def get_available(self) -> list[str]:
        return list(self._translations.keys())

    def get_keys(self, locale: str) -> list[str]:
        return list(self._translations.get(locale, {}).keys())


class RTLLayoutSupport:
    """42. RTL layout support."""

    RTL_LANGUAGES = {"ar", "he", "fa", "ur", "yi", "ps", "sd"}

    def __init__(self):
        self._force_rtl = False

    def is_rtl(self, locale: str) -> bool:
        return self._force_rtl or locale.split("-")[0] in self.RTL_LANGUAGES

    def force_rtl(self, enabled: bool):
        self._force_rtl = enabled

    def get_direction(self, locale: str) -> str:
        return "rtl" if self.is_rtl(locale) else "ltr"

    def get_css(self, locale: str) -> str:
        direction = self.get_direction(locale)
        return f'html[dir="{direction}"] {{ direction: {direction}; }}'

    def mirror_value(self, value: str, locale: str) -> str:
        if self.is_rtl(locale):
            replacements = {"left": "right", "right": "left", "margin-left": "margin-right", "margin-right": "margin-left"}
            for old, new in replacements.items():
                value = value.replace(old, new)
        return value


class DateTimeFormatting:
    """43. Date/time locale formatting."""

    FORMATS = {
        "en": {"date": "%m/%d/%Y", "time": "%I:%M %p", "datetime": "%m/%d/%Y %I:%M %p"},
        "es": {"date": "%d/%m/%Y", "time": "%H:%M", "datetime": "%d/%m/%Y %H:%M"},
        "de": {"date": "%d.%m.%Y", "time": "%H:%M", "datetime": "%d.%m.%Y %H:%M"},
        "ja": {"date": "%Y年%m月%d日", "time": "%H:%M", "datetime": "%Y年%m月%d日 %H:%M"},
        "zh": {"date": "%Y年%m月%d日", "time": "%H:%M", "datetime": "%Y年%m月%d日 %H:%M"},
    }

    def __init__(self):
        self._custom_formats: dict[str, dict] = {}

    def get_format(self, locale: str, fmt_type: str = "date") -> str:
        fmts = self._custom_formats.get(locale, self.FORMATS.get(locale, self.FORMATS["en"]))
        return fmts.get(fmt_type, "%Y-%m-%d")

    def set_format(self, locale: str, fmt_type: str, pattern: str):
        if locale not in self._custom_formats:
            self._custom_formats[locale] = {}
        self._custom_formats[locale][fmt_type] = pattern

    def format_timestamp(self, timestamp: float, locale: str, fmt_type: str = "datetime") -> str:
        from datetime import datetime
        pattern = self.get_format(locale, fmt_type)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime(pattern)


class NumberFormatting:
    """44. Number formatting (currency, decimals)."""

    LOCALES = {
        "en": {"decimal": ".", "thousands": ",", "currency": "$", "currency_after": False},
        "de": {"decimal": ",", "thousands": ".", "currency": "€", "currency_after": True},
        "fr": {"decimal": ",", "thousands": " ", "currency": "€", "currency_after": True},
        "ja": {"decimal": ".", "thousands": ",", "currency": "¥", "currency_after": False},
    }

    def __init__(self):
        self._custom: dict[str, dict] = {}

    def format_number(self, number: float, locale: str, decimals: int = 2) -> str:
        cfg = self._custom.get(locale, self.LOCALES.get(locale, self.LOCALES["en"]))
        parts = f"{number:,.{decimals}f}".split(".")
        integer_part = parts[0].replace(",", cfg["thousands"])
        if len(parts) > 1:
            integer_part = integer_part.replace(",", "")  # Reset then apply locale
            int_str = str(int(abs(number)))
            formatted = ""
            for i, ch in enumerate(reversed(int_str)):
                if i > 0 and i % 3 == 0:
                    formatted = cfg["thousands"] + formatted
                formatted = ch + formatted
            if number < 0:
                formatted = "-" + formatted
            return f"{formatted}{cfg['decimal']}{parts[1][:decimals]}"
        return integer_part

    def format_currency(self, amount: float, locale: str, decimals: int = 2) -> str:
        cfg = self._custom.get(locale, self.LOCALES.get(locale, self.LOCALES["en"]))
        num = self.format_number(amount, locale, decimals)
        if cfg["currency_after"]:
            return f"{num}{cfg['currency']}"
        return f"{cfg['currency']}{num}"

    def set_locale_config(self, locale: str, config: dict):
        self._custom[locale] = config


class PluralizationRules:
    """45. Pluralization rules."""

    def __init__(self):
        self._rules: dict[str, dict] = {
            "en": {"zero": 0, "one": 1, "other": "default"},
            "es": {"zero": 0, "one": 1, "other": "default", "many": ">= 10"},
            "fr": {"zero": 0, "one": 1, "other": "default"},
            "ar": {"zero": 0, "one": 1, "two": 2, "few": "3-10", "many": "11-99", "other": ">= 100"},
            "ja": {"other": "default"},
            "zh": {"other": "default"},
        }

    def get_plural_form(self, count: int, locale: str) -> str:
        if count == 0:
            return "zero"
        if count == 1:
            return "one"
        return "other"

    def pluralize(self, key: str, count: int, locale: str) -> str:
        form = self.get_plural_form(count, locale)
        return f"{key}_{form}"

    def set_rule(self, locale: str, forms: dict):
        self._rules[locale] = forms

    def get_forms(self, locale: str) -> dict:
        return self._rules.get(locale, self._rules["en"])


class ContextAwareTranslations:
    """46. Context-aware translations."""

    def __init__(self):
        self._translations: dict[str, dict[str, str]] = {}

    def add(self, context: str, key: str, value: str):
        if context not in self._translations:
            self._translations[context] = {}
        self._translations[context][key] = value

    def translate(self, context: str, key: str) -> str:
        return self._translations.get(context, {}).get(key, key)

    def t(self, context: str, key: str) -> str:
        return self.translate(context, key)

    def get_contexts(self) -> list[str]:
        return list(self._translations.keys())

    def get_keys(self, context: str) -> list[str]:
        return list(self._translations.get(context, {}).keys())


class TranslationMemory:
    """47. Translation memory."""

    def __init__(self):
        self._memory: dict[str, dict[str, str]] = {}

    def add_pair(self, source: str, target: str, locale: str):
        if locale not in self._memory:
            self._memory[locale] = {}
        self._memory[locale][source] = target

    def lookup(self, source: str, locale: str) -> str | None:
        return self._memory.get(locale, {}).get(source)

    def fuzzy_match(self, source: str, locale: str, threshold: float = 0.8) -> str | None:
        memory = self._memory.get(locale, {})
        best_match = None
        best_score = 0.0
        for s, t in memory.items():
            score = self._similarity(source, s)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = t
        return best_match

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    def get_memory_size(self, locale: str | None = None) -> int:
        if locale:
            return len(self._memory.get(locale, {}))
        return sum(len(v) for v in self._memory.values())


class AutoTranslation:
    """48. Auto-translation (AI)."""

    def __init__(self):
        self._cache: dict[str, str] = {}
        self._supported = ["en", "es", "fr", "de", "ja", "zh", "pt", "it", "ru", "ar"]

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        cache_key = f"{source_lang}:{target_lang}:{text}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        result = f"[auto:{target_lang}]{text}[/auto:{target_lang}]"
        self._cache[cache_key] = result
        return result

    def batch_translate(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        return [self.translate(t, source_lang, target_lang) for t in texts]

    def get_supported_languages(self) -> list[str]:
        return list(self._supported)

    def get_cache_size(self) -> int:
        return len(self._cache)

    def clear_cache(self):
        self._cache.clear()


class LanguageFallbackChain:
    """49. Language fallback chain."""

    def __init__(self):
        self._chains: dict[str, list[str]] = {
            "en-US": ["en", "en-GB", "fr", "es"],
            "en-GB": ["en", "en-US", "fr"],
            "es-MX": ["es", "es-ES", "en", "pt"],
            "pt-BR": ["pt", "pt-PT", "en", "es"],
            "zh-TW": ["zh-CN", "zh", "en"],
        }
        self._default_chain = ["en"]

    def set_chain(self, locale: str, chain: list[str]):
        self._chains[locale] = chain

    def get_chain(self, locale: str) -> list[str]:
        return self._chains.get(locale, [locale] + self._default_chain)

    def resolve(self, locale: str, available: list[str]) -> str:
        chain = self.get_chain(locale)
        for loc in chain:
            if loc in available:
                return loc
        return available[0] if available else locale

    def set_default_chain(self, chain: list[str]):
        self._default_chain = chain


class TranslationQualityScorer:
    """50. Translation quality scoring."""

    def __init__(self):
        self._scores: list[dict] = []

    def score(self, source: str, translation: str, locale: str, translator: str = "auto") -> dict:
        length_ratio = len(translation) / max(len(source), 1)
        has_punctuation = bool(re.search(r'[.!?;,]', translation))
        has_variables = bool(re.search(r'\{[^}]+\}', translation)) if re.search(r'\{[^}]+\}', source) else True
        words = translation.split()
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)

        quality_score = 0
        if 0.5 <= length_ratio <= 2.0:
            quality_score += 30
        if has_punctuation:
            quality_score += 20
        if has_variables:
            quality_score += 25
        if 2 <= avg_word_len <= 12:
            quality_score += 15
        if len(set(words)) / max(len(words), 1) > 0.3:
            quality_score += 10

        result = {
            "source": source,
            "translation": translation,
            "locale": locale,
            "translator": translator,
            "quality_score": quality_score,
            "length_ratio": round(length_ratio, 2),
        }
        self._scores.append(result)
        return result

    def get_average_score(self, locale: str | None = None) -> float:
        relevant = [s for s in self._scores if not locale or s["locale"] == locale]
        if not relevant:
            return 0.0
        return sum(s["quality_score"] for s in relevant) / len(relevant)

    def get_scores(self, limit: int = 100) -> list[dict]:
        return self._scores[-limit:]

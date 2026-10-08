"""Theme engine: 1-10."""

import hashlib
import json
import time


class ThemeEngine:
    """1. Dynamic theme generator from brand colors."""

    def generate_from_brand(self, brand_colors: dict) -> dict:
        primary = brand_colors.get("primary", "#007bff")
        secondary = brand_colors.get("secondary", "#6c757d")
        accent = brand_colors.get("accent", "#28a745")
        background = brand_colors.get("background", "#ffffff")
        text = brand_colors.get("text", "#212529")

        return {
            "name": f"Brand-{hashlib.md5(json.dumps(brand_colors).encode()).hexdigest()[:8]}",
            "primary": primary,
            "secondary": secondary,
            "accent": accent,
            "background": background,
            "text": text,
            "css_variables": {
                "--primary": primary,
                "--secondary": secondary,
                "--accent": accent,
                "--bg": background,
                "--text": text,
            },
        }


class DarkLightMode:
    """2. Dark/Light mode with auto-detect."""

    def __init__(self):
        self._mode = "auto"
        self._last_detect = 0

    def set_mode(self, mode: str):
        if mode not in ("light", "dark", "auto"):
            raise ValueError("mode must be light, dark, or auto")
        self._mode = mode

    def get_mode(self) -> str:
        return self._mode

    def detect_system(self, hour: int | None = None) -> str:
        h = hour if hour is not None else time.localtime().tm_hour
        return "dark" if h < 7 or h >= 19 else "light"

    def resolve(self, hour: int | None = None) -> str:
        if self._mode == "auto":
            return self.detect_system(hour)
        return self._mode


class HighContrastMode:
    """3. High contrast mode (WCAG AAA)."""

    AAA_MIN_RATIO = 7.0

    def enable(self) -> dict:
        return {"contrast_ratio": 21, "mode": "aaa", "foreground": "#000000", "background": "#ffffff"}

    @staticmethod
    def check_ratio(fg_luminance: float, bg_luminance: float) -> float:
        lighter = max(fg_luminance, bg_luminance)
        darker = min(fg_luminance, bg_luminance)
        return (lighter + 0.05) / (darker + 0.05)


class CSSVariableInjector:
    """4. Custom CSS variable injection."""

    def __init__(self):
        self._variables: dict[str, str] = {}

    def inject(self, name: str, value: str):
        if not name.startswith("--"):
            name = f"--{name}"
        self._variables[name] = value

    def inject_many(self, variables: dict[str, str]):
        for k, v in variables.items():
            self.inject(k, v)

    def to_css(self, selector: str = ":root") -> str:
        lines = [f"{selector} {{\n"]
        for k, v in self._variables.items():
            lines.append(f"  {k}: {v};\n")
        lines.append("}")
        return "".join(lines)

    def get_all(self) -> dict:
        return dict(self._variables)


class ThemeMarketplace:
    """5. Theme marketplace (community themes)."""

    def __init__(self):
        self._themes: dict[str, dict] = {}

    def publish(self, theme_id: str, theme: dict, author: str = "anonymous"):
        self._themes[theme_id] = {**theme, "author": author, "downloads": 0, "rating": 0.0}

    def list_themes(self) -> list:
        return [{"id": k, **v} for k, v in self._themes.items()]

    def download(self, theme_id: str) -> dict:
        if theme_id not in self._themes:
            raise KeyError(f"Theme {theme_id} not found")
        self._themes[theme_id]["downloads"] += 1
        return self._themes[theme_id]

    def rate(self, theme_id: str, score: float):
        if theme_id not in self._themes:
            raise KeyError(f"Theme {theme_id} not found")
        self._themes[theme_id]["rating"] = score


class ThemeScheduler:
    """6. Theme scheduler (time-based switching)."""

    def __init__(self):
        self._schedule: list[dict] = []

    def add_rule(self, theme: str, start_hour: int, end_hour: int):
        self._schedule.append({"theme": theme, "start": start_hour, "end": end_hour})

    def get_current_theme(self, hour: int | None = None) -> str | None:
        h = hour if hour is not None else time.localtime().tm_hour
        for rule in self._schedule:
            if rule["start"] <= h < rule["end"]:
                return rule["theme"]
        return self._schedule[0]["theme"] if self._schedule else None

    def list_rules(self) -> list:
        return list(self._schedule)


class ServiceThemeOverrides:
    """7. Per-service theme overrides."""

    def __init__(self):
        self._overrides: dict[str, dict] = {}

    def set_override(self, service: str, theme: dict):
        self._overrides[service] = theme

    def get_override(self, service: str) -> dict | None:
        return self._overrides.get(service)

    def remove_override(self, service: str) -> bool:
        return self._overrides.pop(service, None) is not None

    def list_overrides(self) -> dict:
        return dict(self._overrides)


class AccessibilityFontControls:
    """8. Font size accessibility controls."""

    DEFAULT_SIZES = {"small": 12, "medium": 16, "large": 20, "xlarge": 24}
    MIN_SIZE = 10
    MAX_SIZE = 48

    def __init__(self):
        self._current_size = 16
        self._preset = "medium"

    def set_preset(self, preset: str):
        if preset not in self.DEFAULT_SIZES:
            raise ValueError(f"Preset must be one of: {list(self.DEFAULT_SIZES.keys())}")
        self._preset = preset
        self._current_size = self.DEFAULT_SIZES[preset]

    def set_custom(self, size: int):
        size = max(self.MIN_SIZE, min(self.MAX_SIZE, size))
        self._current_size = size
        self._preset = "custom"

    def get_size(self) -> int:
        return self._current_size

    def get_css(self) -> str:
        return f"html {{ font-size: {self._current_size}px; }}"


class ColorBlindPalette:
    """9. Color blind friendly palette."""

    PALETTES = {
        "protanopia": {"red": "#d55e00", "green": "#009e73", "blue": "#0072b2", "yellow": "#f0e442"},
        "deuteranopia": {"red": "#d55e00", "green": "#009e73", "blue": "#0072b2", "yellow": "#f0e442"},
        "tritanopia": {"red": "#cc79a7", "green": "#009e73", "blue": "#56b4e9", "yellow": "#f0e442"},
        "normal": {"red": "#e41a1c", "green": "#4daf4a", "blue": "#377eb8", "yellow": "#ffff33"},
    }

    def get_palette(self, vision_type: str = "normal") -> dict:
        return self.PALETTES.get(vision_type, self.PALETTES["normal"])

    def suggest_color(self, original: str, vision_type: str) -> str:
        palette = self.get_palette(vision_type)
        color_map = {"#e41a1c": palette["red"], "#4daf4a": palette["green"], "#377eb8": palette["blue"]}
        return color_map.get(original, original)


class ThemePreviewAB:
    """10. Theme preview & A/B testing."""

    def __init__(self):
        self._tests: dict[str, dict] = {}
        self._results: dict[str, dict] = {}

    def create_test(self, test_id: str, theme_a: dict, theme_b: dict, traffic_split: float = 0.5):
        self._tests[test_id] = {"a": theme_a, "b": theme_b, "split": traffic_split, "users_a": 0, "users_b": 0}

    def assign_variant(self, test_id: str, user_id: str) -> str:
        if test_id not in self._tests:
            raise KeyError(f"Test {test_id} not found")
        test = self._tests[test_id]
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
        variant = "a" if hash_val < test["split"] * 100 else "b"
        test[f"users_{variant}"] += 1
        return variant

    def record_conversion(self, test_id: str, variant: str):
        if test_id not in self._results:
            self._results[test_id] = {"a": 0, "b": 0}
        self._results[test_id][variant] += 1

    def get_results(self, test_id: str) -> dict:
        return self._results.get(test_id, {})

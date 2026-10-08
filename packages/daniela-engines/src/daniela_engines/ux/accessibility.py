"""Accessibility: 21-30."""



class WCAGComplianceChecker:
    """21. WCAG 2.1 AA compliance checker."""

    AA_NORMAL_MIN = 4.5
    AA_LARGE_MIN = 3.0
    AAA_NORMAL_MIN = 7.0
    AAA_LARGE_MIN = 4.5

    def check_contrast(self, ratio: float, level: str = "aa", is_large: bool = False) -> dict:
        if level == "aa":
            required = self.AA_LARGE_MIN if is_large else self.AA_NORMAL_MIN
        else:
            required = self.AAA_LARGE_MIN if is_large else self.AAA_NORMAL_MIN
        return {"ratio": ratio, "required": required, "passes": ratio >= required, "level": level}

    def check_element(self, fg: dict, bg: dict) -> dict:
        fg_l = self._relative_luminance(fg.get("r", 0), fg.get("g", 0), fg.get("b", 0))
        bg_l = self._relative_luminance(bg.get("r", 0), bg.get("g", 0), bg.get("b", 0))
        ratio = self._contrast_ratio(fg_l, bg_l)
        return self.check_contrast(ratio)

    @staticmethod
    def _relative_luminance(r: int, g: int, b: int) -> float:
        rs, gs, bs = r / 255.0, g / 255.0, b / 255.0
        r_lin = rs / 12.92 if rs <= 0.04045 else ((rs + 0.055) / 1.055) ** 2.4
        g_lin = gs / 12.92 if gs <= 0.04045 else ((gs + 0.055) / 1.055) ** 2.4
        b_lin = bs / 12.92 if bs <= 0.04045 else ((bs + 0.055) / 1.055) ** 2.4
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

    @staticmethod
    def _contrast_ratio(l1: float, l2: float) -> float:
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)


class ScreenReaderOptimizer:
    """22. Screen reader optimization (ARIA labels)."""

    def __init__(self):
        self._labels: dict[str, str] = {}

    def add_label(self, element_id: str, label: str, role: str = ""):
        self._labels[element_id] = {"label": label, "role": role}

    def get_label(self, element_id: str) -> dict | None:
        return self._labels.get(element_id)

    def generate_aria(self, element_id: str) -> str:
        label_info = self._labels.get(element_id)
        if not label_info:
            return ""
        parts = [f'aria-label="{label_info["label"]}"']
        if label_info["role"]:
            parts.append(f'role="{label_info["role"]}"')
        return " ".join(parts)

    def validate_labels(self, elements: list[dict]) -> list[dict]:
        issues = []
        for el in elements:
            eid = el.get("id", "")
            if not el.get("aria-label") and not el.get("aria-labelledby") and not self._labels.get(eid):
                issues.append({"element": eid, "issue": "missing label"})
        return issues


class KeyboardNavigationManager:
    """23. Keyboard navigation manager."""

    def __init__(self):
        self._bindings: dict[str, str] = {}
        self._tab_order: list[str] = []

    def bind(self, key: str, action: str):
        self._bindings[key] = action

    def unbind(self, key: str) -> bool:
        return self._bindings.pop(key, None) is not None

    def get_action(self, key: str) -> str | None:
        return self._bindings.get(key)

    def set_tab_order(self, elements: list[str]):
        self._tab_order = list(elements)

    def get_tab_order(self) -> list[str]:
        return list(self._tab_order)

    def get_next_focus(self, current: str) -> str | None:
        if current in self._tab_order:
            idx = self._tab_order.index(current)
            next_idx = (idx + 1) % len(self._tab_order)
            return self._tab_order[next_idx]
        return self._tab_order[0] if self._tab_order else None


class FocusTrapManager:
    """24. Focus trap management."""

    def __init__(self):
        self._active_traps: dict[str, list[str]] = {}

    def activate(self, trap_id: str, elements: list[str]):
        self._active_traps[trap_id] = elements

    def deactivate(self, trap_id: str) -> bool:
        return self._active_traps.pop(trap_id, None) is not None

    def is_active(self, trap_id: str) -> bool:
        return trap_id in self._active_traps

    def get_elements(self, trap_id: str) -> list[str]:
        return self._active_traps.get(trap_id, [])

    def get_next(self, trap_id: str, current: str) -> str | None:
        elements = self._active_traps.get(trap_id, [])
        if not elements or current not in elements:
            return elements[0] if elements else None
        idx = elements.index(current)
        return elements[(idx + 1) % len(elements)]

    def get_prev(self, trap_id: str, current: str) -> str | None:
        elements = self._active_traps.get(trap_id, [])
        if not elements or current not in elements:
            return elements[-1] if elements else None
        idx = elements.index(current)
        return elements[(idx - 1) % len(elements)]


class SkipNavigation:
    """25. Skip navigation links."""

    def __init__(self):
        self._links: list[dict] = []

    def add_link(self, label: str, target_id: str):
        self._links.append({"label": label, "target": target_id})

    def get_links(self) -> list[dict]:
        return list(self._links)

    def generate_html(self) -> str:
        items = []
        for link in self._links:
            items.append(f'<a href="#{link["target"]}" class="skip-link">{link["label"]}</a>')
        return "\n".join(items)

    def clear(self):
        self._links.clear()


class AltTextGenerator:
    """26. Alt text generator for images."""

    def __init__(self):
        self._alt_texts: dict[str, str] = {}

    def set_alt(self, image_id: str, text: str):
        self._alt_texts[image_id] = text

    def get_alt(self, image_id: str) -> str:
        return self._alt_texts.get(image_id, "")

    def generate_placeholder(self, image_id: str) -> str:
        return f"Image: {image_id}"

    def validate_images(self, images: list[dict]) -> list[dict]:
        issues = []
        for img in images:
            src = img.get("src", "")
            alt = img.get("alt", "")
            if not alt:
                issues.append({"src": src, "issue": "missing alt text"})
        return issues


class ColorContrastChecker:
    """27. Color contrast checker."""

    def __init__(self):
        self._history: list[dict] = []

    def check(self, fg_color: str, bg_color: str) -> dict:
        fg_rgb = self._hex_to_rgb(fg_color)
        bg_rgb = self._hex_to_rgb(bg_color)
        fg_lum = self._luminance(fg_rgb)
        bg_lum = self._luminance(bg_rgb)
        ratio = (max(fg_lum, bg_lum) + 0.05) / (min(fg_lum, bg_lum) + 0.05)
        result = {"fg": fg_color, "bg": bg_color, "ratio": round(ratio, 2)}
        self._history.append(result)
        return result

    def get_history(self) -> list[dict]:
        return list(self._history)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    @staticmethod
    def _luminance(rgb: tuple[int, int, int]) -> float:
        channels = []
        for c in rgb:
            s = c / 255.0
            channels.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


class MotionReduction:
    """28. Motion reduction toggle."""

    def __init__(self):
        self._enabled: dict[str, bool] = {}
        self._global = False

    def set_global(self, reduce: bool):
        self._global = reduce

    def is_global(self) -> bool:
        return self._global

    def set_user(self, user_id: str, reduce: bool):
        self._enabled[user_id] = reduce

    def should_reduce(self, user_id: str | None = None) -> bool:
        if user_id and user_id in self._enabled:
            return self._enabled[user_id]
        return self._global

    def get_css(self) -> str:
        if self._global:
            return "@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; } }"
        return ""


class TextToSpeech:
    """29. Text-to-speech integration."""

    def __init__(self):
        self._queue: list[dict] = []
        self._settings: dict = {"rate": 1.0, "pitch": 1.0, "volume": 1.0, "voice": "default"}

    def configure(self, **kwargs):
        self._settings.update(kwargs)

    def speak(self, text: str, priority: bool = False):
        item = {"text": text, "settings": dict(self._settings)}
        if priority:
            self._queue.insert(0, item)
        else:
            self._queue.append(item)

    def get_queue(self) -> list[dict]:
        return list(self._queue)

    def pop(self) -> dict | None:
        return self._queue.pop(0) if self._queue else None

    def clear(self):
        self._queue.clear()

    def get_settings(self) -> dict:
        return dict(self._settings)


class VoiceCommandInterface:
    """30. Voice command interface."""

    def __init__(self):
        self._commands: dict[str, str] = {}
        self._listening = False

    def register_command(self, phrase: str, action: str):
        self._commands[phrase.lower()] = action

    def unregister_command(self, phrase: str) -> bool:
        return self._commands.pop(phrase.lower(), None) is not None

    def start_listening(self):
        self._listening = True

    def stop_listening(self):
        self._listening = False

    def is_listening(self) -> bool:
        return self._listening

    def process(self, spoken: str) -> str | None:
        spoken_lower = spoken.lower().strip()
        for phrase, action in self._commands.items():
            if phrase in spoken_lower:
                return action
        return None

    def get_commands(self) -> dict:
        return dict(self._commands)

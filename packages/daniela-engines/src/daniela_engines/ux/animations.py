"""Micro-interactions: 31-40."""

import random


class SkeletonLoader:
    """31. Loading skeleton screens."""

    def __init__(self):
        self._templates: dict[str, list[dict]] = {}

    def define_template(self, name: str, blocks: list[dict]):
        self._templates[name] = blocks

    def get_template(self, name: str) -> list[dict]:
        return self._templates.get(name, [])

    def render(self, name: str) -> str:
        blocks = self._templates.get(name, [])
        lines = ['<div class="skeleton-container">']
        for block in blocks:
            w = block.get("width", "100%")
            h = block.get("height", "20px")
            lines.append(f'  <div class="skeleton-block" style="width:{w};height:{h}"></div>')
        lines.append("</div>")
        return "\n".join(lines)

    def list_templates(self) -> list[str]:
        return list(self._templates.keys())


class PageTransitions:
    """32. Smooth page transitions."""

    PRESETS = {
        "fade": {"duration": 300, "easing": "ease-in-out"},
        "slide-left": {"duration": 400, "easing": "cubic-bezier(0.4, 0, 0.2, 1)"},
        "slide-right": {"duration": 400, "easing": "cubic-bezier(0.4, 0, 0.2, 1)"},
        "zoom": {"duration": 350, "easing": "ease-out"},
        "flip": {"duration": 500, "easing": "ease-in-out"},
    }

    def __init__(self):
        self._custom: dict[str, dict] = {}

    def get_preset(self, name: str) -> dict:
        return self.PRESETS.get(name, self._custom.get(name, self.PRESETS["fade"]))

    def add_custom(self, name: str, config: dict):
        self._custom[name] = config

    def get_css(self, name: str) -> str:
        cfg = self.get_preset(name)
        return f".page-transition {{ transition: opacity {cfg['duration']}ms {cfg['easing']}, transform {cfg['duration']}ms {cfg['easing']}; }}"


class HoverEffectLibrary:
    """33. Hover effect library."""

    EFFECTS = {
        "scale-up": "transform: scale(1.05);",
        "scale-down": "transform: scale(0.95);",
        "glow": "box-shadow: 0 0 20px rgba(0,123,255,0.5);",
        "underline": "text-decoration: underline;",
        "color-shift": "filter: hue-rotate(30deg);",
        "lift": "transform: translateY(-4px); box-shadow: 0 4px 12px rgba(0,0,0,0.15);",
        "border-pulse": "border-color: var(--primary);",
    }

    def get_effect(self, name: str) -> str:
        return self.EFFECTS.get(name, "")

    def list_effects(self) -> list[str]:
        return list(self.EFFECTS.keys())

    def apply_css(self, effect_name: str, selector: str = ".hoverable") -> str:
        css = self.get_effect(effect_name)
        return f"{selector}:hover {{ {css} transition: all 0.2s ease; }}"


class ToastNotificationSystem:
    """34. Toast notification system."""

    def __init__(self):
        self._toasts: list[dict] = []
        self._defaults = {"duration": 3000, "position": "top-right", "type": "info"}

    def configure(self, **kwargs):
        self._defaults.update(kwargs)

    def show(self, message: str, toast_type: str = "info", duration: int | None = None):
        toast = {
            "message": message,
            "type": toast_type,
            "duration": duration or self._defaults["duration"],
            "position": self._defaults["position"],
        }
        self._toasts.append(toast)

    def get_toasts(self) -> list[dict]:
        return list(self._toasts)

    def dismiss(self, index: int) -> bool:
        if 0 <= index < len(self._toasts):
            self._toasts.pop(index)
            return True
        return False

    def clear(self):
        self._toasts.clear()

    def success(self, msg: str):
        self.show(msg, "success")

    def error(self, msg: str):
        self.show(msg, "error")

    def warning(self, msg: str):
        self.show(msg, "warning")


class ProgressBarAnimations:
    """35. Progress bar animations."""

    PRESETS = {
        "linear": "linear",
        "ease-in": "cubic-bezier(0.4, 0, 1, 1)",
        "ease-out": "cubic-bezier(0, 0, 0.2, 1)",
        "bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
    }

    def __init__(self):
        self._bars: dict[str, dict] = {}

    def create(self, bar_id: str, value: float = 0, style: str = "linear"):
        self._bars[bar_id] = {"value": max(0, min(100, value)), "style": style, "animated": True}

    def update(self, bar_id: str, value: float):
        if bar_id in self._bars:
            self._bars[bar_id]["value"] = max(0, min(100, value))

    def get_bar(self, bar_id: str) -> dict:
        return self._bars.get(bar_id, {})

    def get_css(self, bar_id: str) -> str:
        bar = self._bars.get(bar_id, {})
        easing = self.PRESETS.get(bar.get("style", "linear"), "linear")
        return f"transition: width 0.3s {easing};"


class ConfettiAnimation:
    """36. Confetti/success animations."""

    def __init__(self):
        self._particles: list[dict] = []
        self._colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7", "#dda0dd"]

    def trigger(self, count: int = 50):
        self._particles = []
        for _ in range(count):
            self._particles.append({
                "color": random.choice(self._colors),
                "x": random.uniform(0, 100),
                "y": random.uniform(-50, 0),
                "rotation": random.uniform(0, 360),
                "size": random.uniform(4, 12),
            })

    def get_particles(self) -> list[dict]:
        return list(self._particles)

    def is_active(self) -> bool:
        return len(self._particles) > 0

    def clear(self):
        self._particles.clear()


class PullToRefresh:
    """37. Pull-to-refresh animation."""

    def __init__(self):
        self._threshold = 80
        self._refreshing = False
        self._pull_distance = 0

    def set_threshold(self, threshold: int):
        self._threshold = threshold

    def pull(self, distance: int):
        self._pull_distance = distance
        if distance >= self._threshold and not self._refreshing:
            self._refreshing = True

    def is_refreshing(self) -> bool:
        return self._refreshing

    def complete(self):
        self._refreshing = False
        self._pull_distance = 0

    def get_progress(self) -> float:
        return min(1.0, self._pull_distance / self._threshold)


class InfiniteScroll:
    """38. Infinite scroll with skeleton."""

    def __init__(self):
        self._loading = False
        self._items: list[dict] = []
        self._page = 0
        self._has_more = True
        self._page_size = 20

    def set_page_size(self, size: int):
        self._page_size = size

    def load_next(self) -> list[dict]:
        if not self._has_more or self._loading:
            return []
        self._loading = True
        self._page += 1
        start = (self._page - 1) * self._page_size
        end = start + self._page_size
        result = self._items[start:end]
        if end >= len(self._items):
            self._has_more = False
        self._loading = False
        return result

    def add_items(self, items: list[dict]):
        self._items.extend(items)
        self._has_more = True

    def is_loading(self) -> bool:
        return self._loading

    def has_more(self) -> bool:
        return self._has_more

    def reset(self):
        self._loading = False
        self._page = 0
        self._has_more = True


class DragDropAnimations:
    """39. Drag & drop animations."""

    def __init__(self):
        self._dragging = False
        self._source: str | None = None
        self._target: str | None = None
        self._position: dict = {"x": 0, "y": 0}

    def start_drag(self, element_id: str, x: int = 0, y: int = 0):
        self._dragging = True
        self._source = element_id
        self._position = {"x": x, "y": y}

    def move(self, x: int, y: int):
        if self._dragging:
            self._position = {"x": x, "y": y}

    def set_target(self, element_id: str):
        self._target = element_id

    def drop(self) -> tuple[str, str] | None:
        result = None
        if self._dragging and self._source and self._target:
            result = (self._source, self._target)
        self._dragging = False
        self._source = None
        self._target = None
        return result

    def is_dragging(self) -> bool:
        return self._dragging

    def get_position(self) -> dict:
        return dict(self._position)


class NumberCounterAnimation:
    """40. Number counter animation."""

    def __init__(self):
        self._counters: dict[str, dict] = {}

    def create(self, counter_id: str, target: float, duration: int = 1000, decimals: int = 0):
        self._counters[counter_id] = {
            "start": 0,
            "current": 0,
            "target": target,
            "duration": duration,
            "decimals": decimals,
            "steps": max(1, duration // 16),
        }

    def get_frame(self, counter_id: str, frame: int) -> float:
        counter = self._counters.get(counter_id)
        if not counter:
            return 0.0
        progress = min(1.0, frame / counter["steps"])
        eased = 1 - (1 - progress) ** 3
        value = counter["start"] + (counter["target"] - counter["start"]) * eased
        counter["current"] = round(value, counter["decimals"])
        return counter["current"]

    def get_current(self, counter_id: str) -> float:
        counter = self._counters.get(counter_id, {})
        return counter.get("current", 0.0)

    def is_complete(self, counter_id: str, total_frames: int) -> bool:
        counter = self._counters.get(counter_id, {})
        return total_frames >= counter.get("steps", 0)

    def reset(self, counter_id: str):
        if counter_id in self._counters:
            self._counters[counter_id]["current"] = 0

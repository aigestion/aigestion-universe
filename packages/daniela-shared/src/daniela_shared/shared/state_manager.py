import time

from .config import DATA_DIR, load_json, save_json
from .event_bus import bus


class StateManager:
    def __init__(self):
        self._state = load_json(DATA_DIR / "global_state.json", {
            "user": {"name": "Alejandro", "mood": "neutral", "energy": 80},
            "devices": {"pc": {"online": True}, "phone": {"online": False}},
            "context": {"location": "home", "activity": "desktop", "attention": "pc"},
            "focus": {"active": False, "since": None},
            "ambient": {"color": "#00f0ff", "sound": "none", "brightness": 50},
            "last_update": time.time()
        })

    def get(self, key, default=None):
        keys = key.split(".")
        val = self._state
        for k in keys:
            val = val.get(k, {}) if isinstance(val, dict) else default
        return val if isinstance(val, dict) or val is not None else default

    def set(self, key, value):
        keys = key.split(".")
        ref = self._state
        for k in keys[:-1]:
            ref = ref.setdefault(k, {})
        old = ref.get(keys[-1])
        ref[keys[-1]] = value
        self._state["last_update"] = time.time()
        if old != value:
            bus.emit("state.change", {"key": key, "old": old, "new": value})
        save_json(DATA_DIR / "global_state.json", self._state)

    def snapshot(self):
        return self._state.copy()

state = StateManager()

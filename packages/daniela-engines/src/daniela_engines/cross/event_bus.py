"""Central Cross-Engine Event Bus with pub/sub, wildcards, and TTL history."""

import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Optional


class CrossEngineEventBus:
    """Singleton event bus connecting all 19 engines."""

    _instance: Optional["CrossEngineEventBus"] = None
    _lock_class = threading.Lock()

    def __new__(cls) -> "CrossEngineEventBus":
        with cls._lock_class:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._lock = threading.Lock()
        self._subscribers: dict[str, dict[str, list[Callable]]] = {}
        self._history: deque = deque(maxlen=1000)
        self._stats: dict[str, int] = {}
        self._initialized = True

    def publish(self, source_engine: str, event_type: str, payload: dict = None) -> int:
        """Broadcast event to all matching subscribers. Returns count of notified callbacks."""
        event = {
            "source_engine": source_engine,
            "event_type": event_type,
            "payload": payload or {},
            "timestamp": time.time(),
        }
        with self._lock:
            self._history.append(event)
            key = f"{source_engine}:{event_type}"
            self._stats[key] = self._stats.get(key, 0) + 1

        notified = 0
        matched_subs = []
        with self._lock:
            for _engine_name, type_map in self._subscribers.items():
                for pattern, callbacks in type_map.items():
                    if self._matches(pattern, event_type):
                        matched_subs.extend(callbacks)

        for cb in matched_subs:
            try:
                cb(event)
                notified += 1
            except Exception:
                pass
        return notified

    def subscribe(self, engine_name: str, event_type: str, callback: Callable) -> None:
        """Register a listener for an event type (supports wildcards like 'security.*')."""
        with self._lock:
            if engine_name not in self._subscribers:
                self._subscribers[engine_name] = {}
            if event_type not in self._subscribers[engine_name]:
                self._subscribers[engine_name][event_type] = []
            self._subscribers[engine_name][event_type].append(callback)

    def unsubscribe(self, engine_name: str, event_type: str) -> bool:
        """Remove listener(s) for an engine+event_type pair."""
        with self._lock:
            if engine_name in self._subscribers and event_type in self._subscribers[engine_name]:
                del self._subscribers[engine_name][event_type]
                return True
            return False

    def get_events(self, limit: int = 100) -> list[dict]:
        """Return the most recent events up to `limit`."""
        with self._lock:
            items = list(self._history)
        return items[-limit:]

    def get_stats(self) -> dict:
        """Return event counts per engine:type and total."""
        with self._lock:
            stats = dict(self._stats)
        total = sum(stats.values())
        by_engine: dict[str, int] = {}
        for key, count in stats.items():
            engine = key.split(":", 1)[0]
            by_engine[engine] = by_engine.get(engine, 0) + count
        return {"total": total, "by_key": stats, "by_engine": by_engine}

    def reset(self) -> None:
        """Clear all subscribers, history, and stats (used in tests)."""
        with self._lock:
            self._subscribers.clear()
            self._history.clear()
            self._stats.clear()

    @staticmethod
    def _matches(pattern: str, event_type: str) -> bool:
        """Check if an event_type matches a pattern (supports '*')."""
        if pattern == "*":
            return True
        if "*" not in pattern:
            return pattern == event_type
        prefix = pattern.split("*")[0]
        return event_type.startswith(prefix)


def get_event_bus() -> CrossEngineEventBus:
    """Convenience accessor."""
    return CrossEngineEventBus()

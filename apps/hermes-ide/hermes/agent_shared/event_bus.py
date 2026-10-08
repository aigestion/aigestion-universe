import time
from collections import defaultdict


class EventBus:
    def __init__(self):
        self._listeners = defaultdict(list)
        self._history = []

    def on(self, event, callback):
        self._listeners[event].append(callback)

    def emit(self, event, data=None):
        self._history.append({"event": event, "data": data, "time": time.time()})
        if len(self._history) > 500:
            self._history = self._history[-500:]
        for cb in self._listeners.get(event, []):
            try:
                cb(data)
            except Exception:
                pass

    def history(self):
        return self._history[-50:]

bus = EventBus()

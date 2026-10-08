#!/usr/bin/env python3
"""
PA-03: Sensor Stream Live - WebSocket telemetry en tiempo real
==============================================================
Streaming continuo de TODOS los sensores del Pixel al PC via SSE (Server-Sent Events).
El PC polla los sensores del Pixel y los reenvia al navegador en tiempo real.

Sensores: acelerometro, giroscopo, magnetometro, luz, proximidad,
          GPS, bateria, temperatura, nivel de senal, paso.

Rutas registradas en daniela_os.py:
  - /api/pixel/sensors/live  (SSE stream)
  - /api/pixel/sensors       (JSON snapshot)
  - /api/pixel/sensors/history?seconds=60 (historial)

Coste: $0/mes
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import requests

# ── Config ───────────────────────────────────────────────────

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "sensor_stream")
STATE_FILE = os.path.join(STATE_DIR, "sensor_stream_state.json")

# Pixel connection (reuses pixel_bridge_hub config)
GATEWAY_PORT = 8082
AUTH_TOKEN = os.getenv("PIXEL_TOKEN", "")
DISCOVERY_TIMEOUT = 2
REQUEST_TIMEOUT = 5

# Sensor polling
SENSORS_TO_POLL = [
    "accelerometer",
    "gyroscope",
    "magnetometer",
    "light",
    "proximity",
    "step",
]
BATTERY_POLL_INTERVAL = 15  # seconds
LOCATION_POLL_INTERVAL = 30  # seconds
SENSOR_POLL_INTERVAL = 2  # seconds
HISTORY_MAX = 600  # keep 10 minutes of data at 1Hz

# ── Data classes ──────────────────────────────────────────────


@dataclass
class SensorReading:
    timestamp: float
    sensor: str
    values: Dict[str, Any] = field(default_factory=dict)
    source: str = "pixel"  # "pixel" or "pc"


@dataclass
class SensorSnapshot:
    timestamp: float
    accelerometer: Optional[Dict] = None
    gyroscope: Optional[Dict] = None
    magnetometer: Optional[Dict] = None
    light: Optional[Dict] = None
    proximity: Optional[Dict] = None
    step: Optional[Dict] = None
    battery: Optional[Dict] = None
    location: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return asdict(self)


# ── Sensor Stream Live ────────────────────────────────────────


class SensorStreamLive:
    """Polls Pixel sensors and streams them via SSE."""

    def __init__(self, pixel_ip: Optional[str] = None):
        self._pixel_ip = pixel_ip
        self._lock = threading.Lock()
        self._running = False
        self._threads: List[threading.Thread] = []
        self._latest = SensorSnapshot(timestamp=time.time())
        self._history: deque = deque(maxlen=HISTORY_MAX)
        self._subscribers: List[deque] = []
        self._sub_lock = threading.Lock()
        self._error_count = 0
        self._poll_count = 0
        self._start_time = None

    # ── Pixel discovery ───────────────────────────────────────

    def _get_pixel_ip(self) -> Optional[str]:
        if self._pixel_ip:
            return self._pixel_ip
        # Try known IPs
        known = ["192.168.1.133", "192.168.1.170", "192.168.1.100"]
        for ip in known:
            try:
                url = f"http://{ip}:{GATEWAY_PORT}/api/pixel/health"
                r = requests.get(
                    url,
                    headers={"X-Pixel-Token": AUTH_TOKEN},
                    timeout=DISCOVERY_TIMEOUT,
                )
                if r.status_code == 200:
                    self._pixel_ip = ip
                    return ip
            except requests.RequestException:
                continue
        return None

    def _call_pixel(
        self, path: str, method: str = "GET", json_body: Optional[Dict] = None
    ) -> Optional[Dict]:
        ip = self._get_pixel_ip()
        if not ip:
            return None
        url = f"http://{ip}:{GATEWAY_PORT}{path}"
        headers = {"X-Pixel-Token": AUTH_TOKEN}
        try:
            if method == "GET":
                r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            else:
                r = requests.post(
                    url, headers=headers, json=json_body or {}, timeout=REQUEST_TIMEOUT
                )
            if r.status_code == 200:
                return r.json().get("data") or r.json()
        except requests.RequestException:
            self._error_count += 1
        return None

    # ── Polling ───────────────────────────────────────────────

    def _poll_sensor(self, sensor_name: str) -> Optional[Dict]:
        result = self._call_pixel(
            "/api/pixel/sensor",
            method="POST",
            json_body={"sensor": sensor_name, "delay": 100, "count": 1},
        )
        if result and isinstance(result, dict):
            # termux-sensor returns {"sensors": {sensor_name: {...}}}
            sensors = result.get("sensors", result)
            return sensors.get(sensor_name, sensors)
        return None

    def _poll_battery(self) -> Optional[Dict]:
        return self._call_pixel("/api/pixel/battery")

    def _poll_location(self) -> Optional[Dict]:
        return self._call_pixel("/api/pixel/location")

    def _sensor_loop(self):
        """Background thread: poll all sensors every N seconds."""
        while self._running:
            try:
                acc = self._poll_sensor("accelerometer")
                gyro = self._poll_sensor("gyroscope")
                mag = self._poll_sensor("magnetometer")
                light = self._poll_sensor("light")
                prox = self._poll_sensor("proximity")
                step = self._poll_sensor("step")

                with self._lock:
                    self._latest.accelerometer = acc
                    self._latest.gyroscope = gyro
                    self._latest.magnetometer = mag
                    self._latest.light = light
                    self._latest.proximity = prox
                    self._latest.step = step
                    self._latest.timestamp = time.time()
                    self._poll_count += 1

                snapshot = self._latest.to_dict()
                self._history.append(snapshot)
                self._notify_subscribers(snapshot)

            except Exception:
                self._error_count += 1

            time.sleep(SENSOR_POLL_INTERVAL)

    def _battery_loop(self):
        """Background thread: poll battery every N seconds."""
        while self._running:
            try:
                bat = self._poll_battery()
                if bat:
                    with self._lock:
                        self._latest.battery = bat
                        self._latest.timestamp = time.time()
            except Exception:
                self._error_count += 1
            time.sleep(BATTERY_POLL_INTERVAL)

    def _location_loop(self):
        """Background thread: poll GPS every N seconds."""
        while self._running:
            try:
                loc = self._poll_location()
                if loc:
                    with self._lock:
                        self._latest.location = loc
                        self._latest.timestamp = time.time()
            except Exception:
                self._error_count += 1
            time.sleep(LOCATION_POLL_INTERVAL)

    # ── Subscriber management ─────────────────────────────────

    def subscribe(self) -> deque:
        """Subscribe to live sensor updates. Returns a deque to read from."""
        q: deque = deque(maxlen=100)
        with self._sub_lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: deque):
        with self._sub_lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def _notify_subscribers(self, data: Dict):
        with self._sub_lock:
            for q in self._subscribers:
                q.append(data)

    # ── Public API ────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._start_time = time.time()

        t1 = threading.Thread(target=self._sensor_loop, daemon=True, name="sensor-poll")
        t2 = threading.Thread(target=self._battery_loop, daemon=True, name="battery-poll")
        t3 = threading.Thread(target=self._location_loop, daemon=True, name="location-poll")
        self._threads = [t1, t2, t3]
        for t in self._threads:
            t.start()

    def stop(self):
        self._running = False
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=2)

    def get_snapshot(self) -> Dict:
        with self._lock:
            return self._latest.to_dict()

    def get_history(self, seconds: int = 60) -> List[Dict]:
        cutoff = time.time() - seconds
        with self._lock:
            return [s for s in self._history if s.get("timestamp", 0) >= cutoff]

    def get_status(self) -> Dict:
        return {
            "running": self._running,
            "pixel_online": self._pixel_ip is not None,
            "pixel_ip": self._pixel_ip,
            "poll_count": self._poll_count,
            "error_count": self._error_count,
            "uptime": int(time.time() - self._start_time) if self._start_time else 0,
            "history_size": len(self._history),
            "subscriber_count": len(self._subscribers),
        }

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.get_status(), f, indent=2, ensure_ascii=False)


# ── Singleton ─────────────────────────────────────────────────

_instance: Optional[SensorStreamLive] = None


def get_instance() -> SensorStreamLive:
    global _instance
    if _instance is None:
        _instance = SensorStreamLive()
    return _instance


# ── Flask route registration ──────────────────────────────────


def register_sensor_routes(flask_app):
    """Register sensor stream routes in daniela_os.py."""

    @flask_app.route("/api/pixel/sensors")
    def pixel_sensors_snapshot():
        """JSON snapshot of all latest sensor readings."""
        stream = get_instance()
        return flask_app.jsonify(stream.get_snapshot())

    @flask_app.route("/api/pixel/sensors/history")
    def pixel_sensors_history():
        """Historical sensor data for the last N seconds."""
        seconds = int(flask_app.request.args.get("seconds", 60))
        seconds = min(seconds, 600)
        stream = get_instance()
        return flask_app.jsonify(stream.get_history(seconds))

    @flask_app.route("/api/pixel/sensors/live")
    def pixel_sensors_live():
        """SSE stream of live sensor data."""
        stream = get_instance()
        q = stream.subscribe()

        def generate():
            try:
                # Send initial snapshot
                yield f"data: {json.dumps(stream.get_snapshot())}\n\n"
                while True:
                    if q:
                        data = q.popleft()
                        yield f"data: {json.dumps(data)}\n\n"
                    else:
                        # Heartbeat every 15s
                        yield ": heartbeat\n\n"
                    time.sleep(0.5)
            finally:
                stream.unsubscribe(q)

        from flask import Response

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    @flask_app.route("/api/pixel/sensors/status")
    def pixel_sensors_status():
        """Status of the sensor stream service."""
        return flask_app.jsonify(get_instance().get_status())

    print(
        "[Sensor Stream] Routes registered: /api/pixel/sensors/live, /sensors, /sensors/history, /sensors/status"
    )


# ── CLI ───────────────────────────────────────────────────────


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sensor_stream_live.py [status|snapshot|history|start]")
        return

    cmd = sys.argv[1]
    stream = get_instance()

    if cmd == "status":
        stream.start()
        time.sleep(3)
        print(json.dumps(stream.get_status(), indent=2))
        stream.stop()
    elif cmd == "snapshot":
        stream.start()
        time.sleep(5)
        snap = stream.get_snapshot()
        print(json.dumps(snap, indent=2, default=str))
        stream.stop()
    elif cmd == "history":
        stream.start()
        time.sleep(10)
        hist = stream.get_history(10)
        print(f"Got {len(hist)} readings")
        for h in hist[-3:]:
            print(json.dumps(h, default=str))
        stream.stop()
    elif cmd == "start":
        stream.start()
        print("Sensor stream started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(10)
                s = stream.get_status()
                print(
                    f"  polls={s['poll_count']} errors={s['error_count']} online={s['pixel_online']}"
                )
        except KeyboardInterrupt:
            stream.stop()
            print("Stopped.")
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
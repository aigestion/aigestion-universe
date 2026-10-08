#!/usr/bin/env python3
"""
PA-07: Pixel as Security Camera - motion detection + AI vision
==================================================================
Cuando el Pixel esta cargando, usar la camara como camara de seguridad.

Flujo:
  1. Capturar frame cada N segundos (termux-camera-photo)
  2. Comparar con frame anterior (motion detection por diferencia)
  3. Si detecta movimiento:
     a. Guardar foto
     b. Enviar a Gemini Vision para clasificar
        (persona, animal, paquete, intruso, vehiculo, nada)
     c. Si es relevante -> alerta al PC via FCM bridge
     d. Si es intruso -> alerta + sonido + notificacion prioritaria

Motion detection:
  - Comparacion de frames con Pillow (gratis)
  - Threshold configurable (default 5% diferencia)
  - Cooldown entre alertas (evita spam)

Rutas en daniela_os.py:
  - GET  /api/pixel/security/status    (estado)
  - POST /api/pixel/security/start     (iniciar vigilancia)
  - POST /api/pixel/security/stop      (detener)
  - GET  /api/pixel/security/events    (eventos detectados)

Coste: $0/mes (Gemini free tier + Pillow)
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

import requests

# ── Config ───────────────────────────────────────────────────

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "security_cam")
STATE_FILE = os.path.join(STATE_DIR, "security_state.json")
CAPTURE_DIR = os.path.join(STATE_DIR, "captures")
EVENTS_FILE = os.path.join(STATE_DIR, "events.json")

GATEWAY_PORT = 8082
AUTH_TOKEN = os.getenv("PIXEL_TOKEN", "")
DISCOVERY_TIMEOUT = 2
REQUEST_TIMEOUT = 30

KNOWN_IPS = ["192.168.1.133", "192.168.1.170", "192.168.1.100"]

# Motion detection
CAPTURE_INTERVAL = 3  # seconds between captures
MOTION_THRESHOLD = 5.0  # % pixel difference to trigger
ALERT_COOLDOWN = 60  # seconds between alerts (avoid spam)
MAX_EVENTS = 100  # keep last N events

# Gemini Vision classification
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
GEMINI_MODEL = "gemini-2.0-flash"  # free tier, vision capable

CLASSES = ["persona", "animal", "paquete", "intruso", "vehiculo", "nada"]

# ── Data classes ─────────────────────────────────────────────


@dataclass
class SecurityEvent:
    id: str
    timestamp: float
    motion_score: float
    classification: str = ""
    confidence: str = ""
    description: str = ""
    image_path: str = ""
    alerted: bool = False


@dataclass
class SecurityState:
    running: bool = False
    pixel_ip: str = ""
    pixel_online: bool = False
    capture_count: int = 0
    event_count: int = 0
    last_capture: float = 0.0
    last_event: float = 0.0
    last_motion: float = 0.0
    gemini_available: bool = False
    error_count: int = 0
    last_error: str = ""


# ── Security Camera ──────────────────────────────────────────


class SecurityCamera:
    """Pixel camera as AI-powered security camera."""

    def __init__(self):
        self._pixel_ip: Optional[str] = None
        self._state = SecurityState()
        self._lock = threading.Lock()
        self._events: List[SecurityEvent] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._prev_frame: Optional[bytes] = None
        self._last_alert = 0.0
        self._gemini_ok = False
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [STATE_DIR, CAPTURE_DIR]:
            os.makedirs(d, exist_ok=True)

    # ── Pixel discovery ───────────────────────────────────────

    def _get_pixel_ip(self) -> Optional[str]:
        if self._pixel_ip:
            return self._pixel_ip
        for ip in KNOWN_IPS:
            try:
                url = f"http://{ip}:{GATEWAY_PORT}/api/pixel/health"
                r = requests.get(
                    url, headers={"X-Pixel-Token": AUTH_TOKEN}, timeout=DISCOVERY_TIMEOUT
                )
                if r.status_code == 200:
                    self._pixel_ip = ip
                    self._state.pixel_ip = ip
                    self._state.pixel_online = True
                    return ip
            except requests.RequestException:
                continue
        self._state.pixel_online = False
        return None

    # ── Frame capture ─────────────────────────────────────────

    def _capture_frame(self) -> Optional[bytes]:
        """Capture a frame from the Pixel camera."""
        ip = self._get_pixel_ip()
        if not ip:
            return None
        try:
            url = f"http://{ip}:{GATEWAY_PORT}/api/pixel/camera"
            r = requests.post(
                url,
                headers={"X-Pixel-Token": AUTH_TOKEN},
                json={"filename": "sec_frame.jpg"},
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code == 200:
                # The gateway saves the photo; fetch the raw bytes
                # In practice the gateway returns the image path or base64
                data = r.json().get("data", {})
                if isinstance(data, str):
                    return data.encode("utf-8")
                return json.dumps(data).encode("utf-8")
        except requests.RequestException:
            pass
        return None

    # ── Motion detection ─────────────────────────────────────

    def _motion_score(self, frame1: bytes, frame2: bytes) -> float:
        """Compare two frames, return % difference (0-100)."""
        try:
            import io

            from PIL import Image

            img1 = Image.open(io.BytesIO(frame1)).convert("L").resize((64, 64))
            img2 = Image.open(io.BytesIO(frame2)).convert("L").resize((64, 64))

            px1 = list(img1.getdata())
            px2 = list(img2.getdata())

            if len(px1) != len(px2):
                return 0.0

            diff = sum(1 for a, b in zip(px1, px2) if abs(a - b) > 25)
            return (diff / len(px1)) * 100.0
        except ImportError:
            # Pillow not installed, fall back to byte comparison
            if len(frame1) != len(frame2):
                return 100.0
            diff = sum(1 for a, b in zip(frame1, frame2) if a != b)
            return (diff / len(frame1)) * 100.0
        except Exception:
            return 0.0

    # ── Gemini Vision classification ─────────────────────────

    def _classify_with_gemini(self, image_bytes: bytes) -> Dict:
        """Send image to Gemini Vision for classification."""
        if not GEMINI_API_KEY:
            return {"classification": "unknown", "confidence": "n/a", "description": "No API key"}

        try:
            import base64

            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    "Clasifica esta imagen de camara de seguridad en una de estas "
                                    f"categorias: {', '.join(CLASSES)}. "
                                    'Responde SOLO con JSON: {"clase": "...", '
                                    '"confianza": "alta|media|baja", "descripcion": "..."}'
                                )
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": base64.b64encode(image_bytes).decode("utf-8"),
                                }
                            },
                        ]
                    }
                ]
            }

            r = requests.post(url, json=payload, timeout=20)
            if r.status_code != 200:
                return {"classification": "error", "confidence": "n/a", "description": r.text[:100]}

            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            # Extract JSON from response (strip markdown fences)
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            text = text.rstrip("`").strip()

            result = json.loads(text)
            return {
                "classification": result.get("clase", "nada"),
                "confidence": result.get("confianza", "baja"),
                "description": result.get("descripcion", ""),
            }
        except Exception as e:
            return {"classification": "error", "confidence": "n/a", "description": str(e)[:100]}

    # ── Alert ────────────────────────────────────────────────

    def _send_alert(self, event: SecurityEvent):
        """Send alert to PC via FCM bridge."""
        try:
            from bridges.comms.fcm_real_bridge import get_instance as get_bridge

            bridge = get_bridge()
            priority_type = "security_alert" if event.classification == "intruso" else "info"
            bridge.send_to_pixel(
                title=f"Camara: {event.classification}",
                body=event.description[:200] or f"Movimiento detectado ({event.motion_score:.1f}%)",
                ntype=priority_type,
            )
            event.alerted = True
        except Exception:
            pass

    # ── Monitoring loop ──────────────────────────────────────

    def _monitor_loop(self):
        while self._running:
            try:
                frame = self._capture_frame()

                if frame:
                    with self._lock:
                        self._state.capture_count += 1
                        self._state.last_capture = time.time()

                    # Compare with previous frame
                    if self._prev_frame:
                        score = self._motion_score(self._prev_frame, frame)

                        with self._lock:
                            self._state.last_motion = score

                        cooldown_ok = (time.time() - self._last_alert) > ALERT_COOLDOWN

                        if score > MOTION_THRESHOLD and cooldown_ok:
                            # Save capture
                            ts = int(time.time())
                            filepath = os.path.join(CAPTURE_DIR, f"motion_{ts}.jpg")
                            with open(filepath, "wb") as f:
                                f.write(frame)

                            # Create event
                            event_id = f"sec_{ts}"
                            event = SecurityEvent(
                                id=event_id,
                                timestamp=ts,
                                motion_score=score,
                                image_path=filepath,
                            )

                            # Classify with Gemini Vision
                            classification = self._classify_with_gemini(frame)
                            event.classification = classification.get("classification", "nada")
                            event.confidence = classification.get("confidence", "baja")
                            event.description = classification.get("description", "")

                            # Alert if relevant (not "nada")
                            if event.classification not in ("nada", "error", "unknown"):
                                self._send_alert(event)
                                self._last_alert = time.time()

                            self._events.append(event)
                            if len(self._events) > MAX_EVENTS:
                                self._events = self._events[-MAX_EVENTS:]

                            with self._lock:
                                self._state.event_count += 1
                                self._state.last_event = time.time()

                            self._save_events()

                    self._prev_frame = frame

            except Exception as e:
                with self._lock:
                    self._state.error_count += 1
                    self._state.last_error = str(e)[:200]

            time.sleep(CAPTURE_INTERVAL)

    def _save_events(self):
        try:
            with open(EVENTS_FILE, "w", encoding="utf-8") as f:
                json.dump([asdict(e) for e in self._events[-50:]], f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    # ── Public API ───────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._state.running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="security-cam")
        self._thread.start()

    def stop(self):
        self._running = False
        self._state.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def get_state(self) -> Dict:
        with self._lock:
            return asdict(self._state)

    def get_events(self, limit: int = 20) -> List[Dict]:
        return [asdict(e) for e in self._events[-limit:]]

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.get_state(), f, indent=2, ensure_ascii=False)


# ── Singleton ─────────────────────────────────────────────────

_instance: Optional[SecurityCamera] = None


def get_instance() -> SecurityCamera:
    global _instance
    if _instance is None:
        _instance = SecurityCamera()
    return _instance


# ── Flask route registration ──────────────────────────────────


def register_security_routes(flask_app):
    """Register security camera routes in daniela_os.py."""

    @flask_app.route("/api/pixel/security/status")
    def pixel_security_status():
        return flask_app.jsonify(get_instance().get_state())

    @flask_app.route("/api/pixel/security/start", methods=["POST"])
    def pixel_security_start():
        cam = get_instance()
        cam.start()
        return flask_app.jsonify({"ok": True, "message": "Security camera monitoring started"})

    @flask_app.route("/api/pixel/security/stop", methods=["POST"])
    def pixel_security_stop():
        cam = get_instance()
        cam.stop()
        return flask_app.jsonify({"ok": True, "message": "Security camera stopped"})

    @flask_app.route("/api/pixel/security/events")
    def pixel_security_events():
        limit = int(flask_app.request.args.get("limit", 20))
        cam = get_instance()
        events = cam.get_events(limit)
        return flask_app.jsonify({"count": len(events), "events": events})

    print(
        "[Security Camera] Routes registered: /api/pixel/security/* (status, start, stop, events)"
    )


# ── CLI ───────────────────────────────────────────────────────


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python security_camera.py [status|start|events]")
        return

    cmd = sys.argv[1]
    cam = get_instance()

    if cmd == "status":
        print(json.dumps(cam.get_state(), indent=2))
    elif cmd == "start":
        cam.start()
        print("Security camera started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(15)
                s = cam.get_state()
                print(
                    f"  captures={s['capture_count']} events={s['event_count']} motion={s['last_motion']:.1f}%"
                )
        except KeyboardInterrupt:
            cam.stop()
            print("Stopped.")
    elif cmd == "events":
        events = cam.get_events()
        print(f"Events: {len(events)}")
        for e in events:
            print(f"  [{e['classification']}] {e['motion_score']:.1f}% {e['description'][:60]}")
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
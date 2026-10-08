#!/usr/bin/env python3
"""
PA-04: Firebase FCM Real Bridge - push notifications bidireccionales
=====================================================================
Conecta Firebase Cloud Messaging (gratis, Spark plan) para push notifications reales.

Direccion PC -> Pixel:
  - Recordatorios de calendario
  - Resultados de tareas de agentes
  - Alertas de seguridad
  - Comandos de Daniela

Direccion Pixel -> PC:
  - Notificaciones de WhatsApp recibidas
  - SMS entrantes
  - Llamadas perdidas
  - Bateria baja
  - Eventos del sensor (caida, movimiento)

Mecanismo:
  1. PC envia FCM push al Pixel (requiere firebase-admin + credenciales)
  2. Pixel envia eventos al PC via POST /api/pixel/notify/inbound
  3. Fallback: si Firebase no configurado, usa termux-notification via API gateway

Rutas en daniela_os.py:
  - POST /api/pixel/notify          (enviar push al Pixel)
  - POST /api/pixel/notify/inbound  (recibir evento del Pixel)
  - GET  /api/pixel/notify/pending  (eventos pendientes del Pixel)
  - GET  /api/pixel/notify/status   (estado del bridge)

Coste: $0/mes (FCM ilimitado en Spark plan)
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

import requests

# ── Config ───────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "fcm_bridge")
STATE_FILE = os.path.join(STATE_DIR, "fcm_bridge_state.json")
INBOUND_FILE = os.path.join(STATE_DIR, "inbound_events.json")

GATEWAY_PORT = 8082
AUTH_TOKEN = os.getenv("PIXEL_TOKEN", "")
DISCOVERY_TIMEOUT = 2
REQUEST_TIMEOUT = 5

KNOWN_IPS = ["192.168.1.133", "192.168.1.170", "192.168.1.100"]

# Notification types
NOTIFY_TYPES = {
    "reminder": {"priority": "normal", "ttl": 86400},
    "task_result": {"priority": "normal", "ttl": 3600},
    "security_alert": {"priority": "high", "ttl": 86400},
    "emergency": {"priority": "high", "ttl": 86400},
    "command": {"priority": "normal", "ttl": 3600},
    "info": {"priority": "normal", "ttl": 3600},
    "whatsapp": {"priority": "normal", "ttl": 3600},
    "sms": {"priority": "normal", "ttl": 3600},
    "call": {"priority": "high", "ttl": 3600},
    "battery_low": {"priority": "high", "ttl": 600},
    "sensor_event": {"priority": "normal", "ttl": 600},
}


# ── Data classes ──────────────────────────────────────────────


@dataclass
class Notification:
    id: str
    timestamp: float
    direction: str  # "pc->pixel" or "pixel->pc"
    ntype: str
    title: str
    body: str
    data: dict[str, Any] = field(default_factory=dict)
    delivered: bool = False
    method: str = ""  # "fcm" or "termux" or "local"
    error: str = ""


@dataclass
class FCMBridgeState:
    firebase_available: bool = False
    pixel_device_token: str = ""
    pixel_online: bool = False
    pixel_ip: str = ""
    sent_count: int = 0
    received_count: int = 0
    failed_count: int = 0
    last_sent: float = 0.0
    last_received: float = 0.0
    pending_inbound: int = 0


# ── FCM Real Bridge ───────────────────────────────────────────


class FCMRealBridge:
    """Bidirectional push notification bridge between PC and Pixel."""

    def __init__(self):
        self._pixel_ip: str | None = None
        self._state = FCMBridgeState()
        self._lock = threading.Lock()
        self._inbound: deque = deque(maxlen=200)
        self._outbound_log: deque = deque(maxlen=200)
        self._firebase = None
        self._init_firebase()

    def _init_firebase(self):
        """Try to reuse FirebaseRealtimeState from google_free_tier_automations."""
        try:
            from google_free_tier_automations import FirebaseRealtimeState

            self._firebase = FirebaseRealtimeState()
            self._state.firebase_available = self._firebase.app_initialized
        except Exception:
            self._state.firebase_available = False

    # ── Pixel discovery ───────────────────────────────────────

    def _get_pixel_ip(self) -> str | None:
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

    # ── PC -> Pixel (push notifications) ─────────────────────

    def send_to_pixel(
        self,
        title: str,
        body: str,
        ntype: str = "info",
        data: dict | None = None,
    ) -> dict:
        """Send a push notification from PC to Pixel.

        Tries Firebase FCM first, falls back to Termux notification API.
        """
        notif_id = f"pc2px_{int(time.time() * 1000)}"
        notif = Notification(
            id=notif_id,
            timestamp=time.time(),
            direction="pc->pixel",
            ntype=ntype,
            title=title,
            body=body,
            data=data or {},
        )

        result = {"id": notif_id, "method": "", "ok": False}

        # Try Firebase FCM first
        if self._state.firebase_available and self._firebase:
            try:
                fcm_result = self._firebase.send_push_notification(
                    title=title, body=body, topic="pixel_alerts"
                )
                if fcm_result.get("status") == "sent":
                    result["method"] = "fcm"
                    result["ok"] = True
                    result["fcm_id"] = fcm_result.get("message_id", "")
                    notif.delivered = True
                    notif.method = "fcm"
                    with self._lock:
                        self._state.sent_count += 1
                        self._state.last_sent = time.time()
                    self._outbound_log.append(asdict(notif))
                    return result
            except Exception:
                pass  # Fall through to Termux fallback

        # Fallback: Termux notification via API gateway
        ip = self._get_pixel_ip()
        if ip:
            try:
                url = f"http://{ip}:{GATEWAY_PORT}/api/pixel/notify"
                r = requests.post(
                    url,
                    headers={"X-Pixel-Token": AUTH_TOKEN},
                    json={
                        "title": title[:100],
                        "content": body[:500],
                        "priority": NOTIFY_TYPES.get(ntype, {}).get("priority", "normal"),
                    },
                    timeout=REQUEST_TIMEOUT,
                )
                if r.status_code == 200 and r.json().get("ok"):
                    result["method"] = "termux"
                    result["ok"] = True
                    notif.delivered = True
                    notif.method = "termux"
                    with self._lock:
                        self._state.sent_count += 1
                        self._state.last_sent = time.time()
                    self._outbound_log.append(asdict(notif))
                    return result
            except requests.RequestException:
                pass

        # Both methods failed
        notif.delivered = False
        notif.error = "pixel_offline_or_fcm_unavailable"
        result["method"] = "none"
        result["ok"] = False
        result["error"] = notif.error
        with self._lock:
            self._state.failed_count += 1
        self._outbound_log.append(asdict(notif))
        return result

    # ── Pixel -> PC (inbound events) ──────────────────────────

    def receive_from_pixel(
        self,
        ntype: str,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> dict:
        """Receive an event notification from the Pixel."""
        notif_id = f"px2pc_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        notif = Notification(
            id=notif_id,
            timestamp=time.time(),
            direction="pixel->pc",
            ntype=ntype,
            title=title,
            body=body,
            data=data or {},
            delivered=True,
            method="http_post",
        )
        self._inbound.append(asdict(notif))
        with self._lock:
            self._state.received_count += 1
            self._state.last_received = time.time()
            self._state.pending_inbound = len(self._inbound)
        self._save_inbound()
        return {"ok": True, "id": notif_id}

    def get_pending_inbound(self, limit: int = 50) -> list[dict]:
        """Get pending inbound notifications from the Pixel."""
        items = list(self._inbound)[-limit:]
        self._inbound.clear()
        with self._lock:
            self._state.pending_inbound = 0
        return items

    def get_recent_outbound(self, limit: int = 50) -> list[dict]:
        """Get recent outbound notifications sent to the Pixel."""
        return list(self._outbound_log)[-limit:]

    # ── High-level helpers ────────────────────────────────────

    def send_reminder(self, title: str, body: str) -> dict:
        return self.send_to_pixel(title, body, ntype="reminder")

    def send_security_alert(self, title: str, body: str) -> dict:
        return self.send_to_pixel(title, body, ntype="security_alert")

    def send_emergency(self, title: str, body: str) -> dict:
        return self.send_to_pixel(title, body, ntype="emergency")

    def send_task_result(self, agent: str, result: str) -> dict:
        return self.send_to_pixel(f"[{agent}] Tarea completada", result[:200], ntype="task_result")

    # ── State ────────────────────────────────────────────────

    def get_state(self) -> dict:
        with self._lock:
            state = asdict(self._state)
        state["inbound_queue"] = len(self._inbound)
        state["outbound_log"] = len(self._outbound_log)
        return state

    def register_device_token(self, token: str) -> dict:
        """Register the Pixel's FCM device token."""
        self._state.pixel_device_token = token
        return {"ok": True, "token_registered": True}

    def _save_inbound(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        try:
            items = list(self._inbound)
            with open(INBOUND_FILE, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.get_state(), f, indent=2, ensure_ascii=False)


# ── Singleton ─────────────────────────────────────────────────

_instance: FCMRealBridge | None = None


def get_instance() -> FCMRealBridge:
    global _instance
    if _instance is None:
        _instance = FCMRealBridge()
    return _instance


# ── Flask route registration ──────────────────────────────────


def register_fcm_routes(flask_app):
    """Register FCM bridge routes in daniela_os.py."""

    @flask_app.route("/api/pixel/notify", methods=["POST"])
    def pixel_notify_send():
        """Send a push notification to the Pixel."""
        data = flask_app.request.json or {}
        title = data.get("title", "")
        body = data.get("body", data.get("content", ""))
        ntype = data.get("type", data.get("ntype", "info"))
        extra = data.get("data", {})

        if not title:
            return flask_app.jsonify({"ok": False, "error": "Missing 'title'"}), 400

        bridge = get_instance()
        result = bridge.send_to_pixel(title, body, ntype=ntype, data=extra)
        return flask_app.jsonify(result)

    @flask_app.route("/api/pixel/notify/inbound", methods=["POST"])
    def pixel_notify_inbound():
        """Receive an event notification from the Pixel."""
        data = flask_app.request.json or {}
        ntype = data.get("type", data.get("ntype", "info"))
        title = data.get("title", "")
        body = data.get("body", data.get("content", ""))
        extra = data.get("data", {})

        if not title:
            return flask_app.jsonify({"ok": False, "error": "Missing 'title'"}), 400

        bridge = get_instance()
        result = bridge.receive_from_pixel(ntype, title, body, data=extra)
        return flask_app.jsonify(result)

    @flask_app.route("/api/pixel/notify/pending")
    def pixel_notify_pending():
        """Get pending inbound notifications from the Pixel."""
        bridge = get_instance()
        items = bridge.get_pending_inbound()
        return flask_app.jsonify({"count": len(items), "notifications": items})

    @flask_app.route("/api/pixel/notify/recent")
    def pixel_notify_recent():
        """Get recent outbound notifications sent to the Pixel."""
        bridge = get_instance()
        items = bridge.get_recent_outbound()
        return flask_app.jsonify({"count": len(items), "notifications": items})

    @flask_app.route("/api/pixel/notify/status")
    def pixel_notify_status():
        """FCM bridge status."""
        return flask_app.jsonify(get_instance().get_state())

    @flask_app.route("/api/pixel/notify/register", methods=["POST"])
    def pixel_notify_register():
        """Register Pixel FCM device token."""
        token = (flask_app.request.json or {}).get("token", "")
        if not token:
            return flask_app.jsonify({"ok": False, "error": "Missing 'token'"}), 400
        bridge = get_instance()
        result = bridge.register_device_token(token)
        return flask_app.jsonify(result)

    print(
        "[FCM Bridge] Routes registered: /api/pixel/notify, /notify/inbound, /notify/pending, /notify/recent, /notify/status, /notify/register"
    )


# ── CLI ───────────────────────────────────────────────────────


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fcm_real_bridge.py [status|send <title> <body>|inbound|recent]")
        return

    cmd = sys.argv[1]
    bridge = get_instance()

    if cmd == "status":
        print(json.dumps(bridge.get_state(), indent=2))
    elif cmd == "send":
        title = sys.argv[2] if len(sys.argv) > 2 else "Test"
        body = sys.argv[3] if len(sys.argv) > 3 else "Test notification from PC"
        result = bridge.send_to_pixel(title, body, ntype="info")
        print(json.dumps(result, indent=2))
    elif cmd == "inbound":
        items = bridge.get_pending_inbound()
        print(f"Pending inbound: {len(items)}")
        for item in items:
            print(f"  [{item['ntype']}] {item['title']}: {item['body'][:80]}")
    elif cmd == "recent":
        items = bridge.get_recent_outbound()
        print(f"Recent outbound: {len(items)}")
        for item in items:
            print(
                f"  [{item['ntype']}] {item['title']}: {item['body'][:80]} (delivered={item['delivered']}, method={item['method']})"
            )
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()

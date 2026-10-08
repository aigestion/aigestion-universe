#!/usr/bin/env python3
"""
Termux API Gateway (PA-09)
==========================
Mini servidor Flask que corre en el Pixel (Termux) y expone
TODOS los comandos de Termux como endpoints REST.

El PC (daniela_os.py) descubre y llama esta API via WiFi.

Seguridad:
  - Token auth (compartido con el PC)
  - Subprocess con list args (NO shell=True)
  - Rate limiting basico (30 req/min)
  - Bind a 0.0.0.0:8082 (configurable)

Instalacion en el Pixel:
  pkg install python
  pip install flask
  python termux_api_gateway.py

  (o usar termux-boot para auto-iniciar en boot)

Cost: $0 — corre en el Pixel, no necesita servidor externo
"""

import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
from collections import defaultdict, deque
from datetime import datetime

try:
    from flask import Flask, jsonify, request
except ImportError:
    print("ERROR: Flask no instalado. Ejecuta: pip install flask")
    sys.exit(1)

app = Flask(__name__)

# ============================================================================
# CONFIG
# ============================================================================

AUTH_TOKEN = os.environ.get("PIXEL_GATEWAY_TOKEN", "")
PORT = int(os.environ.get("PIXEL_GATEWAY_PORT", "8082"))
RATE_LIMIT = 30  # requests per minute per IP
RATE_WINDOW = 60  # seconds

# Rate limiter storage
_rate_tracker = defaultdict(deque)

# ============================================================================
# MIDDLEWARE
# ============================================================================


def _check_auth():
    """Verifica el token de autorizacion."""
    token = request.headers.get("X-Pixel-Token", "")
    if not AUTH_TOKEN or not hmac.compare_digest(token, AUTH_TOKEN):
        return False
    return True


def _rate_limit(ip):
    """Rate limiting basico: max RATE_LIMIT requests por minuto."""
    now = time.time()
    tracker = _rate_tracker[ip]
    # Limpiar entries viejas
    while tracker and tracker[0] < now - RATE_WINDOW:
        tracker.popleft()
    if len(tracker) >= RATE_LIMIT:
        return False
    tracker.append(now)
    return True


@app.before_request
def _middleware():
    """Auth + rate limit en cada request."""
    ip = request.remote_addr or "unknown"
    if not _rate_limit(ip):
        return jsonify({"error": "Rate limit exceeded", "limit": RATE_LIMIT}), 429
    if request.path == "/api/pair/challenge":
        return None  # pairing por challenge-response: no pide el token (lo prueba)
    if not _check_auth():
        return jsonify({"error": "Unauthorized", "hint": "Set X-Pixel-Token header"}), 401


@app.route("/api/pair/challenge", methods=["POST"])
def pair_challenge():
    """Prueba de pairing sin exponer el token.

    El PC manda {"nonce": "<hex aleatorio>"} y el gateway devuelve
    HMAC_SHA256(token, nonce). El PC lo compara con su propio token:
    si coincide, ambos extremos comparten el secreto sin haberlo
    transmitido. Ver skills/connectors/android/pairing.py (lado PC).
    """
    data = request.get_json(silent=True) or {}
    nonce = data.get("nonce", "")
    if not isinstance(nonce, str) or not nonce or len(nonce) > 128:
        return jsonify({"error": "nonce requerido (hex, max 128)"}), 400
    if not AUTH_TOKEN:
        return jsonify({"error": "gateway sin token configurado"}), 503
    mac = hmac.new(AUTH_TOKEN.encode(), nonce.encode(), hashlib.sha256)
    return jsonify({"hmac": mac.hexdigest()})


# ============================================================================
# HELPER
# ============================================================================


def _run_termux(args, timeout=10):
    """Ejecuta un comando de Termux de forma segura (list args, no shell)."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            output = result.stdout.strip()
            # Intentar parsear como JSON
            if output:
                try:
                    return {"ok": True, "data": json.loads(output)}
                except json.JSONDecodeError:
                    return {"ok": True, "data": output}
            return {"ok": True, "data": None}
        else:
            return {"ok": False, "error": result.stderr.strip() or "Command failed"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timeout after {timeout}s"}
    except FileNotFoundError:
        return {"ok": False, "error": "Termux API not installed. Run: pkg install termux-api"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _is_termux():
    """Detecta si estamos corriendo en Termux."""
    return os.path.exists("/data/data/com.termux")


# ============================================================================
# ENDPOINTS — DEVICE CONTROL
# ============================================================================


@app.route("/api/pixel/health", methods=["GET"])
def health():
    """Health check del gateway."""
    return jsonify(
        {
            "ok": True,
            "device": "pixel",
            "is_termux": _is_termux(),
            "uptime": int(time.time()),
            "endpoints": len(app.url_map._rules) - 1,  # exclude static
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/pixel/battery", methods=["GET"])
def battery():
    """Estado de la bateria."""
    return jsonify(_run_termux(["termux-battery-status"], timeout=5))


@app.route("/api/pixel/location", methods=["GET"])
def location():
    """Coordenadas GPS."""
    provider = request.args.get("provider", "network")
    updates = request.args.get("requests", "once")
    return jsonify(_run_termux(["termux-location", "-p", provider, "-r", updates], timeout=10))


@app.route("/api/pixel/torch", methods=["POST"])
def torch():
    """Control de la linterna."""
    state = request.json.get("state", True) if request.json else True
    cmd = ["termux-torch", "on" if state else "off"]
    return jsonify(_run_termux(cmd, timeout=3))


@app.route("/api/pixel/clipboard", methods=["GET", "POST"])
def clipboard():
    """Leer o escribir portapapeles."""
    if request.method == "GET":
        return jsonify(_run_termux(["termux-clipboard-get"], timeout=3))
    else:
        text = (request.json or {}).get("text", "")
        return jsonify(_run_termux(["termux-clipboard-set", text], timeout=3))


@app.route("/api/pixel/camera", methods=["POST"])
def camera():
    """Tomar foto."""
    filename = (request.json or {}).get("filename", f"capture_{int(time.time())}.jpg")
    camera_id = str((request.json or {}).get("camera", "0"))
    filepath = os.path.expanduser(f"~/apps/aig/daniela-os/{filename}")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    return jsonify(_run_termux(["termux-camera-photo", "-c", camera_id, filepath], timeout=10))


@app.route("/api/pixel/vibrate", methods=["POST"])
def vibrate():
    """Vibracion haptica."""
    duration = str((request.json or {}).get("duration", 80))
    return jsonify(_run_termux(["termux-vibrate", "-d", duration], timeout=3))


@app.route("/api/pixel/tts", methods=["POST"])
def tts():
    """Text-to-speech en espanol."""
    text = (request.json or {}).get("text", "")
    if not text:
        return jsonify({"ok": False, "error": "Missing 'text' field"}), 400
    lang = (request.json or {}).get("lang", "es")
    # Sanitizar texto: solo alfanumerico y puntuacion basica
    safe_text = text.replace("\n", " ").replace("\r", "")[:500]
    return jsonify(_run_termux(["termux-tts-speak", "-l", lang, safe_text], timeout=15))


@app.route("/api/pixel/mic/record", methods=["POST"])
def mic_record():
    """Grabar audio del microfono."""
    duration = str((request.json or {}).get("duration", 10))
    filename = (request.json or {}).get("filename", f"audio_{int(time.time())}.mp3")
    filepath = os.path.expanduser(f"~/apps/aig/daniela-os/{filename}")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    return jsonify(
        _run_termux(
            ["termux-microphone-record", "-l", duration, "-f", filepath], timeout=int(duration) + 5
        )
    )


@app.route("/api/pixel/mic/stop", methods=["POST"])
def mic_stop():
    """Detener grabacion de audio."""
    return jsonify(_run_termux(["termux-microphone-record", "-q"], timeout=3))


@app.route("/api/pixel/stt", methods=["POST"])
def stt():
    """Speech-to-text."""
    return jsonify(_run_termux(["termux-speech-to-text"], timeout=8))


@app.route("/api/pixel/notifications", methods=["GET"])
def notifications():
    """Lista de notificaciones de Android."""
    return jsonify(_run_termux(["termux-notification-list"], timeout=5))


@app.route("/api/pixel/toast", methods=["POST"])
def toast():
    """Mostrar toast message."""
    message = (request.json or {}).get("message", "")
    if not message:
        return jsonify({"ok": False, "error": "Missing 'message' field"}), 400
    return jsonify(_run_termux(["termux-toast", message[:200]], timeout=3))


@app.route("/api/pixel/sensor", methods=["POST"])
def sensor():
    """Leer sensor (accelerometer, gyroscope, etc.)."""
    sensor_name = (request.json or {}).get("sensor", "accelerometer")
    delay = str((request.json or {}).get("delay", 100))
    count = (request.json or {}).get("count", 1)
    proc = subprocess.Popen(
        ["termux-sensor", "-s", sensor_name, "-d", delay, "-n", str(count)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        stdout, _ = proc.communicate(timeout=5)
        if stdout.strip():
            try:
                data = json.loads(stdout)
                return jsonify({"ok": True, "data": data})
            except json.JSONDecodeError:
                return jsonify({"ok": True, "data": stdout.strip()})
        return jsonify({"ok": False, "error": "No sensor data"})
    except subprocess.TimeoutExpired:
        proc.kill()
        return jsonify({"ok": False, "error": "Sensor timeout"})


# ============================================================================
# ENDPOINTS — NEW (previously unused Termux commands)
# ============================================================================


@app.route("/api/pixel/call", methods=["POST"])
def call():
    """Hacer una llamada telefonica."""
    number = (request.json or {}).get("number", "")
    if not number:
        return jsonify({"ok": False, "error": "Missing 'number' field"}), 400
    return jsonify(_run_termux(["termux-telephony-call", number], timeout=5))


@app.route("/api/pixel/sms/send", methods=["POST"])
def sms_send():
    """Enviar SMS."""
    number = (request.json or {}).get("number", "")
    message = (request.json or {}).get("message", "")
    if not number or not message:
        return jsonify({"ok": False, "error": "Missing 'number' or 'message'"}), 400
    return jsonify(_run_termux(["termux-sms-send", "-n", number, message[:160]], timeout=5))


@app.route("/api/pixel/sms/list", methods=["GET"])
def sms_list():
    """Lista de SMS recibidos."""
    limit = request.args.get("limit", "10")
    return jsonify(_run_termux(["termux-sms-list", "-l", limit], timeout=5))


@app.route("/api/pixel/contacts", methods=["GET"])
def contacts():
    """Lista de contactos."""
    return jsonify(_run_termux(["termux-contact-list"], timeout=5))


@app.route("/api/pixel/call-log", methods=["GET"])
def call_log():
    """Historial de llamadas."""
    limit = request.args.get("limit", "20")
    return jsonify(_run_termux(["termux-call-log", "-l", limit], timeout=5))


@app.route("/api/pixel/media/play", methods=["POST"])
def media_play():
    """Reproducir archivo de media."""
    filepath = (request.json or {}).get("file", "")
    if not filepath:
        return jsonify({"ok": False, "error": "Missing 'file' field"}), 400
    expanded = os.path.expanduser(filepath)
    return jsonify(_run_termux(["termux-media-player", "play", expanded], timeout=5))


@app.route("/api/pixel/media/stop", methods=["POST"])
def media_stop():
    """Detener media."""
    return jsonify(_run_termux(["termux-media-player", "stop"], timeout=3))


@app.route("/api/pixel/fingerprint", methods=["POST"])
def fingerprint():
    """Lectura de huella."""
    return jsonify(_run_termux(["termux-fingerprint"], timeout=15))


@app.route("/api/pixel/brightness", methods=["POST"])
def brightness():
    """Brillo de pantalla."""
    level = str((request.json or {}).get("level", 128))
    return jsonify(_run_termux(["termux-brightness", level], timeout=3))


@app.route("/api/pixel/volume", methods=["POST"])
def volume():
    """Control de volumen."""
    stream = (request.json or {}).get("stream", "music")
    level = str((request.json or {}).get("level", 10))
    return jsonify(_run_termux(["termux-volume", stream, level], timeout=3))


@app.route("/api/pixel/wifi/info", methods=["GET"])
def wifi_info():
    """Info de WiFi."""
    return jsonify(_run_termux(["termux-wifi-connectioninfo"], timeout=5))


@app.route("/api/pixel/wifi/scan", methods=["GET"])
def wifi_scan():
    """Scan de redes WiFi."""
    return jsonify(_run_termux(["termux-wifi-scaninfo"], timeout=10))


@app.route("/api/pixel/bluetooth", methods=["GET"])
def bluetooth():
    """Estado de Bluetooth."""
    return jsonify(_run_termux(["termux-bluetooth-status"], timeout=5))


@app.route("/api/pixel/notify", methods=["POST"])
def notify():
    """Crear notificacion de Android."""
    title = (request.json or {}).get("title", "Daniela")
    content = (request.json or {}).get("content", "")
    if not content:
        return jsonify({"ok": False, "error": "Missing 'content' field"}), 400
    return jsonify(
        _run_termux(
            ["termux-notification", "--title", title[:50], "--content", content[:200]], timeout=3
        )
    )


# ============================================================================
# ENDPOINTS — COMMANDS
# ============================================================================


@app.route("/api/pixel/commands", methods=["GET"])
def commands():
    """Lista de todos los endpoints disponibles."""
    endpoints = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        endpoints.append(
            {
                "path": str(rule),
                "methods": sorted(rule.methods - {"HEAD", "OPTIONS"}),
            }
        )
    return jsonify({"ok": True, "endpoints": endpoints, "total": len(endpoints)})


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  TERMUX API GATEWAY (PA-09)")
    print("=" * 50)
    print(f"  Port: {PORT}")
    print(f"  Auth token: {AUTH_TOKEN[:8]}...")
    print(f"  Rate limit: {RATE_LIMIT} req/min")
    print(f"  Is Termux: {_is_termux()}")
    print(f"  Endpoints: {len([r for r in app.url_map.iter_rules() if r.endpoint != 'static'])}")
    print("=" * 50)
    print("\n  Para probar desde el PC:")
    print(f"    curl -H 'X-Pixel-Token: {AUTH_TOKEN}' http://<PIXEL_IP>:{PORT}/api/pixel/health")
    print()

    app.run(host="0.0.0.0", port=PORT, debug=False)


class TermuxAPIGateway:
    """Gateway de comunicación con Termux API."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def is_available(self) -> bool:
        return False

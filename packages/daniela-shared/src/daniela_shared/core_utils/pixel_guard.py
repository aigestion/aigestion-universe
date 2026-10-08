"""
E-40 + E-41: Pixel Guard — modo degradado honesto + reconexión automática

Intercepts all /api/pixel/* routes. When the Pixel phone is unreachable,
returns 503 with structured context instead of opaque errors.

E-41 adds: automatic reconnection detection, reconnection log, manual
reconnect endpoint, and offline duration tracking.
"""

import os
import threading
import time
import urllib.error
import urllib.request

from flask import Blueprint, jsonify

pixel_guard_bp = Blueprint("pixel_guard", __name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# 2026-09-23: la IP del Pixel cambia (DHCP:.170 -> .133 probado). Se lee de
# entorno (.env PIXEL_GATEWAY_URL o PIXEL_IP) con fallback al ultimo valor.
def _pixel_base():
    url = (os.getenv("PIXEL_GATEWAY_URL", "") or "").strip().strip('"').strip("'")
    if url:
        return url.rstrip("/")
    ip = (os.getenv("PIXEL_IP", "") or "").strip() or "192.168.1.133"
    port = (os.getenv("PIXEL_GATEWAY_PORT", "") or "").strip() or "8082"
    return f"http://{ip}:{port}"


PIXEL_IP = "192.168.1.170"
PIXEL_PORT = 8082
PIXEL_URL = _pixel_base()
CHECK_INTERVAL = 30  # seconds between health pings
CHECK_TIMEOUT = 3    # seconds per ping

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

_state = {
    "online": False,
    "last_seen": 0.0,
    "last_check": 0.0,
    "last_error": "",
    "check_count": 0,
    "fail_streak": 0,
    "uptime_since": 0.0,
    "offline_since": 0.0,
    "total_offline_time": 0.0,
    "reconnect_count": 0,
}

# E-41: Reconnection log (capped at 50 entries)
_reconnect_log = []
MAX_LOG = 50

_lock = threading.Lock()
_stop_event = threading.Event()


def _ping_pixel():
    """Single health ping to the Pixel Termux gateway."""
    try:
        req = urllib.request.Request(
            f"{_pixel_base()}/api/status",
            method="GET",
        )
        resp = urllib.request.urlopen(req, timeout=CHECK_TIMEOUT)
        resp.read()
        return True, ""
    except urllib.error.HTTPError as e:
        # Even a 400/404 means the host is alive
        if e.code < 500:
            return True, ""
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:200]


def _check_loop():
    """Background thread: ping Pixel every CHECK_INTERVAL seconds."""
    while not _stop_event.is_set():
        ok, err = _ping_pixel()
        now = time.time()
        with _lock:
            _state["last_check"] = now
            _state["check_count"] += 1
            was_online = _state["online"]

            if ok:
                _state["online"] = True
                _state["last_seen"] = now
                _state["last_error"] = ""
                _state["fail_streak"] = 0
                if _state["uptime_since"] == 0.0:
                    _state["uptime_since"] = now
                # E-41: Detect reconnection
                if not was_online and _state["offline_since"] > 0.0:
                    down_duration = now - _state["offline_since"]
                    _state["total_offline_time"] += down_duration
                    _state["reconnect_count"] += 1
                    entry = {
                        "event": "reconnected",
                        "time": now,
                        "down_seconds": round(down_duration, 1),
                        "reconnect_number": _state["reconnect_count"],
                    }
                    _reconnect_log.append(entry)
                    if len(_reconnect_log) > MAX_LOG:
                        _reconnect_log.pop(0)
                    print(f"[PixelGuard] RECONNECTED after {down_duration:.0f}s offline "
                          f"(#{_state['reconnect_count']})")
                _state["offline_since"] = 0.0
            else:
                _state["fail_streak"] += 1
                _state["last_error"] = err
                # Go offline after 2 consecutive failures (avoid flapping)
                if _state["fail_streak"] >= 2:
                    if was_online:
                        _state["offline_since"] = now
                        entry = {
                            "event": "went_offline",
                            "time": now,
                            "error": err,
                        }
                        _reconnect_log.append(entry)
                        if len(_reconnect_log) > MAX_LOG:
                            _reconnect_log.pop(0)
                        print(f"[PixelGuard] OFFLINE — {err}")
                    _state["online"] = False
                    _state["uptime_since"] = 0.0
        _stop_event.wait(CHECK_INTERVAL)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

_thread = None


def start_guard():
    """Start the background Pixel health checker."""
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    # Initial check (non-blocking)
    ok, err = _ping_pixel()
    now = time.time()
    with _lock:
        _state["last_check"] = now
        _state["check_count"] = 1
        if ok:
            _state["online"] = True
            _state["last_seen"] = now
            _state["uptime_since"] = now
            _state["offline_since"] = 0.0
        else:
            _state["online"] = False
            _state["last_error"] = err
            _state["fail_streak"] = 1
            _state["offline_since"] = now
    _thread = threading.Thread(target=_check_loop, daemon=True, name="pixel-guard")
    _thread.start()
    status = "ONLINE" if _state["online"] else "OFFLINE"
    print(f"[PixelGuard] Started — Pixel {status} ({PIXEL_URL})")


def stop_guard():
    """Stop the background checker."""
    _stop_event.set()


def get_state():
    """Return a snapshot of the guard state (thread-safe)."""
    with _lock:
        return dict(_state)


def is_online():
    """Quick check: is the Pixel reachable?"""
    with _lock:
        return _state["online"]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@pixel_guard_bp.route("/api/pixel/status")
def pixel_status():
    """Public status of the Pixel guard — always 200."""
    s = get_state()
    return jsonify({
        "pixel_online": s["online"],
        "last_seen": s["last_seen"],
        "last_check": s["last_check"],
        "last_error": s["last_error"],
        "check_count": s["check_count"],
        "fail_streak": s["fail_streak"],
        "uptime_since": s["uptime_since"],
        "offline_since": s["offline_since"] or None,
        "reconnect_count": s["reconnect_count"],
        "total_offline_time": s["total_offline_time"],
        "pixel_url": _pixel_base(),
        "message": (
            "Pixel is reachable" if s["online"]
            else "Pixel is OFFLINE — all /api/pixel/* routes return 503"
        ),
    })


@pixel_guard_bp.route("/api/pixel/health")
def pixel_health():
    """Health endpoint: 200 if online, 503 if offline."""
    s = get_state()
    if s["online"]:
        return jsonify({"status": "ok", "pixel": "online"})
    return jsonify({
        "status": "degraded",
        "pixel": "offline",
        "reason": s["last_error"] or "Pixel unreachable",
        "last_seen": s["last_seen"],
        "how_to_fix": (
            "1) Ensure Pixel is on same WiFi network\n"
            "2) Open Termux on Pixel and run: termux-api-start\n"
            "3) Verify gateway at http://192.168.1.170:8082/api/status\n"
            "4) Or configure Tailscale for remote access"
        ),
    }), 503


@pixel_guard_bp.route("/api/pixel/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def pixel_catch_all(subpath):
    """
    Catch-all for any /api/pixel/* route not explicitly registered.

    If the Pixel is online, this returns a helpful message (the actual
    route handler should have been registered instead). If offline,
    returns 503 with context.
    """
    s = get_state()

    if s["online"]:
        # Pixel is up but this specific route wasn't registered
        return jsonify({
            "error": "route_not_registered",
            "pixel": "online",
            "attempted": f"/api/pixel/{subpath}",
            "message": (
                "The Pixel is reachable but this route is not registered "
                "in the current Daniela build. The route may exist in the "
                "legacy aig/ package."
            ),
        }), 404

    # Pixel is down
    return jsonify({
        "error": "pixel_offline",
        "status": "service_unavailable",
        "pixel": "offline",
        "attempted": f"/api/pixel/{subpath}",
        "reason": s["last_error"] or "Pixel unreachable",
        "last_seen": s["last_seen"],
        "offline_seconds": round(time.time() - s["last_seen"]) if s["last_seen"] else None,
        "how_to_fix": (
            "1) Ensure Pixel is on same WiFi network\n"
            "2) Open Termux on Pixel and run: termux-api-start\n"
            "3) Verify gateway at http://192.168.1.170:8082/api/status\n"
            "4) Or configure Tailscale for remote access"
        ),
    }), 503


# ---------------------------------------------------------------------------
# E-41: Reconnection routes
# ---------------------------------------------------------------------------

@pixel_guard_bp.route("/api/pixel/reconnect", methods=["POST"])
def pixel_reconnect():
    """
    Force an immediate reconnection check.

    POST /api/pixel/reconnect
    Triggers a health ping right now (doesn't wait for the next interval).
    Returns the result of the check.
    """
    ok, err = _ping_pixel()
    now = time.time()
    with _lock:
        was_online = _state["online"]
        _state["last_check"] = now
        _state["check_count"] += 1

        if ok:
            _state["online"] = True
            _state["last_seen"] = now
            _state["last_error"] = ""
            _state["fail_streak"] = 0
            if _state["uptime_since"] == 0.0:
                _state["uptime_since"] = now
            if not was_online and _state["offline_since"] > 0.0:
                down_duration = now - _state["offline_since"]
                _state["total_offline_time"] += down_duration
                _state["reconnect_count"] += 1
                entry = {
                    "event": "reconnected_manual",
                    "time": now,
                    "down_seconds": round(down_duration, 1),
                    "reconnect_number": _state["reconnect_count"],
                }
                _reconnect_log.append(entry)
                if len(_reconnect_log) > MAX_LOG:
                    _reconnect_log.pop(0)
            _state["offline_since"] = 0.0
        else:
            _state["fail_streak"] += 1
            _state["last_error"] = err
            if _state["fail_streak"] >= 2 and was_online:
                _state["offline_since"] = now
                entry = {"event": "went_offline", "time": now, "error": err}
                _reconnect_log.append(entry)
                if len(_reconnect_log) > MAX_LOG:
                    _reconnect_log.pop(0)
            if _state["fail_streak"] >= 2:
                _state["online"] = False
                _state["uptime_since"] = 0.0

    return jsonify({
        "pixel_online": _state["online"],
        "check_time": now,
        "result": "online" if ok else "offline",
        "error": err or None,
        "message": "Pixel is reachable" if ok else f"Pixel unreachable: {err}",
    })


@pixel_guard_bp.route("/api/pixel/reconnect/log")
def pixel_reconnect_log():
    """
    View the reconnection history.

    GET /api/pixel/reconnect/log
    Returns the last 50 reconnection events (online/offline transitions).
    """
    with _lock:
        log = list(_reconnect_log)
        s = dict(_state)

    return jsonify({
        "events": log,
        "total_events": len(log),
        "reconnect_count": s["reconnect_count"],
        "total_offline_time": s["total_offline_time"],
        "currently": "online" if s["online"] else "offline",
        "offline_since": s["offline_since"] or None,
    })

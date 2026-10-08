"""
E-45: /api/health — healthcheck honesto para Daniela Omnipresente.

Devuelve 200 si todo está bien, 503 si algo crítico falla.
Un monitor puede detectar el estado sin leer el body (solo mirar HTTP status).
"""

import time
import urllib.error
import urllib.request

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

# Subsystems to check
_AI_URL = "http://localhost:9200/api/ai/health"
_PIXEL_URL = "http://localhost:9200/api/pixel/status"
_CACHE = {"last_check": 0.0, "result": None, "ttl": 15.0}


def _check_ai():
    """Check if the AI bridge (FreeLLMAPI) is functional."""
    try:
        req = urllib.request.Request(_AI_URL, method="GET")
        urllib.request.urlopen(req, timeout=3)
        return True, "ok"
    except urllib.error.HTTPError as e:
        if e.code == 200:
            return True, "ok"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:100]


def _check_pixel():
    """Check if the Pixel guard reports online."""
    try:
        import json
        resp = urllib.request.urlopen(_PIXEL_URL, timeout=3)
        data = json.loads(resp.read())
        return data.get("pixel_online", False), "online" if data.get("pixel_online") else "offline"
    except Exception as e:
        return False, str(e)[:100]


def _run_checks():
    """Run all health checks. Returns (status_code, body_dict)."""
    now = time.time()

    # Use cache if fresh
    if _CACHE["result"] and (now - _CACHE["last_check"]) < _CACHE["ttl"]:
        return _CACHE["result"]

    checks = {}

    # 1. Core: server is running (always true if we're here)
    checks["core"] = {"status": "ok", "message": "Server is running"}

    # 2. AI bridge
    ai_ok, ai_msg = _check_ai()
    checks["ai"] = {
        "status": "ok" if ai_ok else "critical",
        "message": ai_msg,
    }

    # 3. Pixel guard
    pixel_ok, pixel_msg = _check_pixel()
    checks["pixel"] = {
        "status": "ok" if pixel_ok else "degraded",
        "message": pixel_msg,
    }

    # Determine overall status
    critical_failures = [k for k, v in checks.items() if v["status"] == "critical"]
    degraded = [k for k, v in checks.items() if v["status"] == "degraded"]

    if critical_failures:
        overall = "critical"
        http_status = 503
    elif degraded:
        overall = "degraded"
        http_status = 200  # degraded is not a failure
    else:
        overall = "healthy"
        http_status = 200

    result = {
        "status": overall,
        "timestamp": now,
        "subsystems": checks,
        "summary": {
            "healthy": sum(1 for v in checks.values() if v["status"] == "ok"),
            "degraded": len(degraded),
            "critical": len(critical_failures),
            "total": len(checks),
        },
    }

    _CACHE["last_check"] = now
    _CACHE["result"] = (http_status, result)
    return http_status, result


@health_bp.route("/api/health")
def health():
    """
    GET /api/health

    Returns:
        200 if all subsystems are healthy or degraded
        503 if any critical subsystem is down

    A monitor should check only the HTTP status code, not the body.
    """
    http_status, result = _run_checks()
    return jsonify(result), http_status


@health_bp.route("/api/health/<subsystem>")
def health_subsystem(subsystem):
    """
    GET /api/health/<subsystem>

    Check a specific subsystem: ai, pixel, core
    """
    http_status, result = _run_checks()
    subs = result.get("subsystems", {})
    if subsystem not in subs:
        return jsonify({
            "error": "unknown_subsystem",
            "available": list(subs.keys()),
        }), 404
    return jsonify({
        "subsystem": subsystem,
        **subs[subsystem],
    })

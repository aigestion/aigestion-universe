"""Unified Dashboard — monitoring + WebSocket for Daniela Omnipresente.

Absorbs the unified-dashboard service into Daniela as a blueprint.
Provides real-time service monitoring via WebSocket and REST endpoints.
"""

import json
import socket as _socket
import threading
import time
import urllib.request

from flask import Blueprint, jsonify

# Service definitions — the 18 AIG services
SERVICES = [
    {"id": "epic_pc", "name": "Epic PC", "port": 5020, "category": "Core", "status_path": "/api/status"},
    {"id": "hermes", "name": "Hermes Epic", "port": 9300, "category": "Core", "status_path": "/api/status"},
    {"id": "frontend", "name": "Frontend", "port": 9500, "category": "Frontend", "status_path": "/api/frontend/status"},
    {"id": "optimization", "name": "AIG Optimization", "port": 9400, "category": "Infra", "status_path": "/api/opt/status"},
    {"id": "infra_opt", "name": "Infra Optimization", "port": 9700, "category": "Infra", "status_path": "/api/infra/status"},
    {"id": "daniela", "name": "Daniela Omnipresente", "port": 9200, "category": "AI", "status_path": "/api/status"},
    {"id": "agent_mobile", "name": "Agent & Mobile", "port": 9800, "category": "AI", "status_path": "/api/agent/status"},
    {"id": "auto_engine", "name": "Auto Engine", "port": 9860, "category": "AI", "status_path": "/api/auto/status"},
    {"id": "security", "name": "Security & Monitoring", "port": 9999, "category": "Security", "status_path": "/api/secure/status"},
    {"id": "secure_engine", "name": "Secure Engine", "port": 9880, "category": "Security", "status_path": "/api/secure_engine/status"},
    {"id": "perf", "name": "Performance & Quality", "port": 9998, "category": "Perf", "status_path": "/api/perf/status"},
    {"id": "intel_engine", "name": "Intel Engine", "port": 9850, "category": "Intelligence", "status_path": "/api/intel/status"},
    {"id": "data_engine", "name": "Data Engine", "port": 9870, "category": "Intelligence", "status_path": "/api/data/status"},
    {"id": "devtools_engine", "name": "DevTools Engine", "port": 9890, "category": "Intelligence", "status_path": "/api/devtools/status"},
    {"id": "ecosystem_engine", "name": "Ecosystem Engine", "port": 9840, "category": "Intelligence", "status_path": "/api/ecosystem/status"},
    {"id": "ux_engine", "name": "UX Engine", "port": 9830, "category": "Intelligence", "status_path": "/api/ux/status"},
    {"id": "scale_engine", "name": "Scale Engine", "port": 9820, "category": "Intelligence", "status_path": "/api/scale/status"},
]

# In-memory cache
status_cache = {}
cache_lock = threading.Lock()
socketio = None


def check_service(svc):
    """Check a single service via TCP + HTTP."""
    try:
        sock = _socket.socket()
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', svc["port"]))
        sock.close()
        if result != 0:
            return {"status": "offline", "port": svc["port"]}

        status_path = svc.get("status_path", "/api/status")
        req = urllib.request.Request(f'http://localhost:{svc["port"]}{status_path}')
        req.add_header('User-Agent', 'AIG-Daniela/1.0')
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return {**data, "status": "online", "port": svc["port"]}
    except Exception as e:
        return {"status": "offline", "port": svc["port"], "error": str(e)}
    return {"status": "offline", "port": svc["port"]}


def get_all_status():
    """Get cached status of all services."""
    with cache_lock:
        return {
            "services": SERVICES,
            "status": status_cache,
            "timestamp": time.time(),
            "summary": {
                "total": len(SERVICES),
                "online": sum(1 for s in status_cache.values() if s.get("status") == "online"),
                "offline": sum(1 for s in status_cache.values() if s.get("status") == "offline"),
            },
        }


def _background_poller():
    """Background thread that polls all services every 5 seconds."""
    while True:
        for svc in SERVICES:
            result = check_service(svc)
            with cache_lock:
                status_cache[svc["id"]] = result
        if socketio:
            socketio.emit('status_update', get_all_status())
        time.sleep(5)


def create_dashboard_blueprint(sio=None):
    """Create the monitoring blueprint. Call with the SocketIO instance."""
    global socketio
    socketio = sio

    bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

    @bp.route("/services")
    def api_services():
        return jsonify(get_all_status())

    @bp.route("/services/<service_id>")
    def api_service(service_id):
        with cache_lock:
            if service_id in status_cache:
                return jsonify(status_cache[service_id])
            return jsonify({"error": "Not found"}), 404

    @bp.route("/registry")
    def api_registry():
        registered = []
        for svc in SERVICES:
            if status_cache.get(svc["id"], {}).get("status") == "online":
                registered.append({
                    "name": svc["id"],
                    "port": svc["port"],
                    "category": svc["category"],
                })
        return jsonify({"registered": registered})

    @bp.route("/events")
    def api_events():
        events = []
        for svc in SERVICES:
            if status_cache.get(svc["id"], {}).get("status") == "online":
                events.extend(status_cache[svc["id"]].get("recent_events", []))
        return jsonify({"events": events})

    @bp.route("/gateway")
    def api_gateway_status():
        try:
            req = urllib.request.Request('http://localhost:8080/api/status')
            req.add_header('User-Agent', 'AIG-Daniela/1.0')
            with urllib.request.urlopen(req, timeout=3) as resp:
                return jsonify(json.loads(resp.read().decode()))
        except Exception as e:
            return jsonify({"status": "offline", "error": str(e)}), 503

    @bp.route("/cross")
    def api_cross_status():
        try:
            req = urllib.request.Request('http://localhost:9900/api/status')
            req.add_header('User-Agent', 'AIG-Daniela/1.0')
            with urllib.request.urlopen(req, timeout=3) as resp:
                return jsonify(json.loads(resp.read().decode()))
        except Exception as e:
            return jsonify({"status": "offline", "error": str(e)}), 503

    return bp


def start_poller():
    """Start the background service poller."""
    t = threading.Thread(target=_background_poller, daemon=True)
    t.start()
    return t

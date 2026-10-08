# -*- coding: utf-8 -*-
import sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, DASHROOT)

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO
from aig_shared.auth.middleware import create_auth_middleware
import threading
import time
import json

app = Flask(__name__, static_folder="../dist", static_url_path="/")
CORS(app, origins=["http://localhost:9200", "http://localhost:9300", "http://localhost:9400", "http://localhost:9500"])
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:9200", "http://localhost:9300", "http://localhost:9400", "http://localhost:9500"], async_mode="threading")
create_auth_middleware(app, public_paths={"/api/services", "/api/events"})

# Service configuration with custom status endpoints
SERVICES = [
    # Core
    {"id": "epic_pc", "name": "Epic PC", "port": 5020, "category": "Core", "status_path": "/api/status"},
    {"id": "dashboard", "name": "Unified Dashboard", "port": 9997, "category": "Core", "status_path": "/api/status"},
    {"id": "hermes", "name": "Hermes Epic", "port": 9300, "category": "Core", "status_path": "/api/status"},
    # Frontend
    {"id": "frontend", "name": "Frontend", "port": 9500, "category": "Frontend", "status_path": "/api/frontend/status"},
    # Infra
    {"id": "optimization", "name": "AIG Optimization", "port": 9400, "category": "Infra", "status_path": "/api/opt/status"},
    {"id": "infra_opt", "name": "Infra Optimization", "port": 9700, "category": "Infra", "status_path": "/api/infra/status"},
    # AI
    {"id": "daniela", "name": "Daniela Omnipresente", "port": 9200, "category": "AI", "status_path": "/api/status"},
    {"id": "agent_mobile", "name": "Agent & Mobile", "port": 9800, "category": "AI", "status_path": "/api/agent/status"},
    {"id": "auto_engine", "name": "Auto Engine", "port": 9860, "category": "AI", "status_path": "/api/auto/status"},
    # Security
    {"id": "security", "name": "Security & Monitoring", "port": 9999, "category": "Security", "status_path": "/api/secure/status"},
    {"id": "secure_engine", "name": "Secure Engine", "port": 9880, "category": "Security", "status_path": "/api/secure-engine/status"},
    # Perf
    {"id": "perf", "name": "Performance & Quality", "port": 9998, "category": "Perf", "status_path": "/api/perf/status"},
    # Intelligence
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

def check_service(svc):
    import urllib.request
    import socket
    try:
        # Quick TCP check first
        sock = socket.socket()
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', svc["port"]))
        sock.close()
        if result != 0:
            return {"status": "offline", "port": svc["port"]}
        
        # HTTP check with service-specific endpoint
        status_path = svc.get("status_path", "/api/status")
        req = urllib.request.Request(f'http://localhost:{svc["port"]}{status_path}')
        req.add_header('User-Agent', 'AIG-Dashboard/1.0')
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return {**data, "status": "online", "port": svc["port"]}
    except Exception as e:
        return {"status": "offline", "port": svc["port"], "error": str(e)}
    return {"status": "offline", "port": svc["port"]}

def background_poller():
    while True:
        for svc in SERVICES:
            result = check_service(svc)
            with cache_lock:
                status_cache[svc["id"]] = result
        # Emit status update via WebSocket
        socketio.emit('status_update', get_all_status())
        time.sleep(5)

def get_all_status():
    with cache_lock:
        return {
            "services": SERVICES,
            "status": status_cache,
            "timestamp": time.time(),
            "summary": {
                "total": len(SERVICES),
                "online": sum(1 for s in status_cache.values() if s.get("status") == "online"),
                "offline": sum(1 for s in status_cache.values() if s.get("status") == "offline")
            }
        }

# Start background poller
poller_thread = threading.Thread(target=background_poller, daemon=True)
poller_thread.start()

@app.route("/")
def index():
    return send_from_directory("../dist", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("../dist", path)

@app.route("/api/services")
def api_services():
    return jsonify(get_all_status())

@app.route("/api/services/<service_id>")
def api_service(service_id):
    with cache_lock:
        if service_id in status_cache:
            return jsonify(status_cache[service_id])
        return jsonify({"error": "Not found"}), 404

@app.route("/api/status")
def api_status():
    with cache_lock:
        online = sum(1 for s in status_cache.values() if s.get("status") == "online")
        return jsonify({
            "name": "Unified Dashboard",
            "services": len(SERVICES),
            "online": online,
            "status": "alive"
        })

@app.route("/api/registry")
def api_registry():
    """Get registered services from all services."""
    registered = []
    for svc in SERVICES:
        if status_cache.get(svc["id"], {}).get("status") == "online":
            registered.append({
                "name": svc["id"],
                "port": svc["port"],
                "category": svc["category"],
                "registry": status_cache[svc["id"]].get("registry", "unknown"),
                "events": status_cache[svc["id"]].get("events", "unknown")
            })
    return jsonify({"registered": registered})

@app.route("/api/events")
def api_events():
    """Get recent events from all services."""
    events = []
    for svc in SERVICES:
        if status_cache.get(svc["id"], {}).get("status") == "online":
            events.extend(status_cache[svc["id"]].get("recent_events", []))
    return jsonify({"events": events})

@app.route("/api/gateway/status")
def api_gateway_status():
    """Proxy to Gateway on port 8080."""
    import urllib.request
    try:
        req = urllib.request.Request('http://localhost:8080/api/status')
        req.add_header('User-Agent', 'AIG-Dashboard/1.0')
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return jsonify(data)
    except Exception as e:
        return jsonify({"status": "offline", "error": str(e)}), 503

@app.route("/api/cross/status")
def api_cross_status():
    """Proxy to Cross-Engine on port 9900."""
    import urllib.request
    try:
        req = urllib.request.Request('http://localhost:9900/api/status')
        req.add_header('User-Agent', 'AIG-Dashboard/1.0')
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return jsonify(data)
    except Exception as e:
        return jsonify({"status": "offline", "error": str(e)}), 503

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    socketio.emit('status_update', get_all_status())

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('request_status')
def handle_request_status():
    socketio.emit('status_update', get_all_status())

if __name__ == "__main__":
    print("[Unified Dashboard] Starting on port 9997...")
    socketio.run(app, host="0.0.0.0", port=9997, debug=False, allow_unsafe_werkzeug=True)
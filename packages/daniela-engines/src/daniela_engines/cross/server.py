"""Standalone Cross-Engine Orchestrator Server on port 9900."""

import json
import threading
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

from core.auth.casbin_auth import create_auth_middleware

from .event_bus import get_event_bus
from .orchestrator import CrossEngineOrchestrator
from .protocols import ENGINE_PORTS

app = Flask(__name__)
CORS(app, origins=["http://localhost:9200", "http://localhost:9300", "http://localhost:9400", "http://localhost:9500"])
# Los endpoints de estado/monitorizacion son publicos: los healthchecks de
# Docker y el health gate no llevan JWT. El resto de /api/* sigue protegido.
create_auth_middleware(
    app,
    public_paths={"/api/cross/status", "/api/cross/health", "/health"},
)

_orchestrator = CrossEngineOrchestrator()
_event_bus = get_event_bus()

_ws_clients: list = []
_ws_lock = threading.Lock()


def _broadcast_ws(data: dict):
    """Send event to all WebSocket clients (best-effort)."""
    msg = json.dumps(data)
    with _ws_lock:
        dead = []
        for ws in _ws_clients:
            try:
                ws.send(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _ws_clients.remove(ws)


@app.route("/api/cross/status", methods=["GET"])
def cross_status():
    status = _orchestrator.get_system_status()
    status["health_score"] = _orchestrator.get_system_health()
    status["timestamp"] = time.time()
    status["version"] = "1.0.0"
    return jsonify(status)


@app.route("/api/cross/health", methods=["GET"])
def cross_health():
    return jsonify({
        "health_score": _orchestrator.get_system_health(),
        "engines": _orchestrator.get_system_status()["engines"],
    })


@app.route("/api/cross/events", methods=["GET"])
def cross_events():
    limit = request.args.get("limit", 100, type=int)
    events = _event_bus.get_events(limit=limit)
    return jsonify(events)


@app.route("/api/cross/flows", methods=["GET"])
def cross_flows():
    return jsonify(_orchestrator.get_cross_engine_flows())


@app.route("/api/cross/dependencies", methods=["GET"])
def cross_dependencies():
    return jsonify(_orchestrator.get_engine_dependencies())


@app.route("/api/cross/engine/<name>", methods=["GET"])
def cross_engine_detail(name):
    if name not in ENGINE_PORTS:
        return jsonify({"error": "unknown engine", "name": name}), 404
    status = _orchestrator._check_engine(name)
    status["dependencies"] = _orchestrator.get_engine_dependencies().get(name, [])
    return jsonify(status)


@app.route("/api/cross/anomalies", methods=["GET"])
def cross_anomalies():
    return jsonify(_orchestrator.get_anomalies())


@app.route("/api/cross/stats", methods=["GET"])
def cross_stats():
    return jsonify(_event_bus.get_stats())


@app.route("/ws", methods=["GET"])
def websocket_endpoint():
    """WebSocket upgrade endpoint (HTTP fallback for environments without WS support)."""
    return jsonify({
        "message": "WebSocket endpoint. Use ws://host:9900/ws for real-time updates.",
        "protocol": "ws",
    })


@app.route("/api/cross/flow", methods=["POST"])
def record_flow():
    """Record a data flow between two engines."""
    data = request.get_json(silent=True) or {}
    source = data.get("source")
    target = data.get("target")
    event_type = data.get("event_type", "integration.sync.completed")
    if not source or not target:
        return jsonify({"error": "source and target required"}), 400
    _orchestrator.record_flow(source, target, event_type, data.get("payload"))
    return jsonify({"recorded": True})


@app.route("/api/cross/publish", methods=["POST"])
def publish_event():
    """Publish an event to the bus."""
    data = request.get_json(silent=True) or {}
    source = data.get("source_engine", "unknown")
    event_type = data.get("event_type", "service.health")
    payload = data.get("payload", {})
    notified = _event_bus.publish(source, event_type, payload)
    return jsonify({"notified": notified})


def _start_event_forwarder():
    """Forward bus events to WebSocket clients."""
    def _listener(event):
        _broadcast_ws(event)
    for category in ["service", "data", "security", "workflow", "ai", "scale", "ux", "integration", "devtools"]:
        _event_bus.subscribe("ws_forwarder", f"{category}.*", _listener)


def run_server(host: str = "0.0.0.0", port: int = 9900) -> None:
    """Start the cross-engine orchestrator server."""
    _orchestrator.start()
    _start_event_forwarder()
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    import os
    run_server(port=int(os.getenv("SERVICE_PORT", "9900")))

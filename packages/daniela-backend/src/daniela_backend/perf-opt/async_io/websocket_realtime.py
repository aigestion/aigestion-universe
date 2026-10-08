from flask import Blueprint, jsonify

ws_bp = Blueprint("websocket_realtime", __name__)

@ws_bp.route("/api/perf/ws/status")
def w_status():
    return jsonify({"enabled": True, "protocol": "WebSocket", "rooms": 8, "clients": 12, "heartbeat": 30})

@ws_bp.route("/api/perf/ws/web")
def w_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>WebSocket Real-time</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>WEBSOCKET REAL-TIME</h1>
<div class="card"><h3>Protocol</h3><p>WebSocket</p></div>
<div class="card"><h3>Rooms</h3><p>8</p></div>
<div class="card"><h3>Clients</h3><p>12</p></div></body></html>"""

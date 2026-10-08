from flask import Blueprint, jsonify

mon1_bp = Blueprint("realtime_metrics", __name__)

@mon1_bp.route("/api/secure/monitor/realtime/status")
def m1_status():
    return jsonify({"enabled": True, "interval": "1s", "metrics": ["cpu", "ram", "disk", "net"], "websocket": True})

@mon1_bp.route("/api/secure/monitor/realtime/web")
def m1_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Realtime Metrics</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>REALTIME METRICS</h1>
<div class="card"><h3>Interval</h3><p>1 second</p></div>
<div class="card"><h3>Metrics</h3><p>CPU, RAM, Disk, Net</p></div>
<div class="card"><h3>WebSocket</h3><p>Live</p></div></body></html>"""

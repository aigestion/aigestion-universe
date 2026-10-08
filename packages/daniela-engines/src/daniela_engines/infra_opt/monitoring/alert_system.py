from flask import Blueprint, jsonify

al_bp = Blueprint("alert_system", __name__)

@al_bp.route("/api/infra/monitor/alert/status")
def a_status():
    return jsonify({"enabled": True, "channels": ["telegram", "slack"], "thresholds": {"latency": 500, "errors": 5, "ports": 3}})

@al_bp.route("/api/infra/monitor/alert/web")
def a_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Alert System</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>ALERT SYSTEM</h1>
<div class="card"><h3>Channels</h3><p>Telegram, Slack</p></div>
<div class="card"><h3>Latency</h3><p>>500ms</p></div>
<div class="card"><h3>Errors</h3><p>>5/min</p></div>
<div class="card"><h3>Ports</h3><p>3+ down</p></div></body></html>"""

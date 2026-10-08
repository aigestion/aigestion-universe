from flask import Blueprint, jsonify

ka_bp = Blueprint("connection_keepalive", __name__)

@ka_bp.route("/api/perf/keepalive/status")
def k_status():
    return jsonify({"enabled": True, "timeout": 65, "max_requests": 1000, "tcp_keepalive": True})

@ka_bp.route("/api/perf/keepalive/web")
def k_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Connection Keep-Alive</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>CONNECTION KEEP-ALIVE</h1>
<div class="card"><h3>Timeout</h3><p>65s</p></div>
<div class="card"><h3>Max Requests</h3><p>1000</p></div>
<div class="card"><h3>TCP Keep-Alive</h3><p>Enabled</p></div></body></html>"""

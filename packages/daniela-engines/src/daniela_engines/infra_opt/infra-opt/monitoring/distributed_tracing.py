from flask import Blueprint, jsonify

dt_bp = Blueprint("distributed_tracing", __name__)

@dt_bp.route("/api/infra/monitor/tracing/status")
def d_status():
    return jsonify({"enabled": True, "backend": "Jaeger", "services": 6, "trace_rate": 0.1})

@dt_bp.route("/api/infra/monitor/tracing/web")
def d_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Distributed Tracing</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>DISTRIBUTED TRACING</h1>
<div class="card"><h3>Backend</h3><p>Jaeger</p></div>
<div class="card"><h3>Services</h3><p>6 traced</p></div>
<div class="card"><h3>Trace Rate</h3><p>10% sample</p></div></body></html>"""

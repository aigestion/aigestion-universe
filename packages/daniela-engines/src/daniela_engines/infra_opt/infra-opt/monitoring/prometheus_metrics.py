from flask import Blueprint, jsonify

prom_bp = Blueprint("prometheus_metrics", __name__)

@prom_bp.route("/api/infra/monitor/prom/status")
def p_status():
    return jsonify({"enabled": True, "port": 9090, "metrics": 25, "endpoint": "/metrics"})

@prom_bp.route("/api/infra/monitor/prom/web")
def p_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Prometheus</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>PROMETHEUS METRICS</h1>
<div class="card"><h3>Port</h3><p>9090</p></div>
<div class="card"><h3>Metrics</h3><p>25 defined</p></div>
<div class="card"><h3>Endpoint</h3><p>/metrics</p></div></body></html>"""

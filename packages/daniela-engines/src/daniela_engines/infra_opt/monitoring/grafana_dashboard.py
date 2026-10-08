from flask import Blueprint, jsonify

graf_bp = Blueprint("grafana_dashboard", __name__)

@graf_bp.route("/api/infra/monitor/grafana/status")
def g_status():
    return jsonify({"enabled": True, "url": "http://localhost:3000", "panels": 12, "datasource": "Prometheus"})

@graf_bp.route("/api/infra/monitor/grafana/web")
def g_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Grafana</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>GRAFANA DASHBOARD</h1>
<div class="card"><h3>URL</h3><p>http://localhost:3000</p></div>
<div class="card"><h3>Panels</h3><p>12</p></div>
<div class="card"><h3>Datasource</h3><p>Prometheus</p></div></body></html>"""

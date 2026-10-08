from flask import Blueprint, jsonify

mon3_bp = Blueprint("log_aggregator", __name__)

@mon3_bp.route("/api/secure/monitor/log/status")
def m3_status():
    return jsonify({"enabled": True, "sources": 6, "format": "JSON", "retention": 90})

@mon3_bp.route("/api/secure/monitor/log/web")
def m3_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Log Aggregator</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>LOG AGGREGATOR</h1>
<div class="card"><h3>Sources</h3><p>6 services</p></div>
<div class="card"><h3>Format</h3><p>JSON</p></div>
<div class="card"><h3>Retention</h3><p>90 days</p></div></body></html>"""

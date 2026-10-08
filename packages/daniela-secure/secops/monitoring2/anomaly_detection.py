from flask import Blueprint, jsonify

mon2_bp = Blueprint("anomaly_detection", __name__)

@mon2_bp.route("/api/secure/monitor/anomaly/status")
def m2_status():
    return jsonify({"enabled": True, "algorithm": "ML", "thresholds": {"latency": 500, "errors": 5}, "alert": True})

@mon2_bp.route("/api/secure/monitor/anomaly/web")
def m2_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Anomaly Detection</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>ANOMALY DETECTION</h1>
<div class="card"><h3>Algorithm</h3><p>ML-based</p></div>
<div class="card"><h3>Latency</h3><p>>500ms</p></div>
<div class="card"><h3>Errors</h3><p>>5/min</p></div></body></html>"""

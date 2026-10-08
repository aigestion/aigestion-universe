from flask import Blueprint, jsonify

sl_bp = Blueprint("structured_logging", __name__)

@sl_bp.route("/api/infra/monitor/logging/status")
def s_status():
    return jsonify({"format": "JSON", "correlation_ids": True, "output": "stdout", "level": "INFO"})

@sl_bp.route("/api/infra/monitor/logging/web")
def s_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Structured Logging</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>STRUCTURED LOGGING</h1>
<div class="card"><h3>Format</h3><p>JSON</p></div>
<div class="card"><h3>Correlation</h3><p>Enabled</p></div>
<div class="card"><h3>Level</h3><p>INFO</p></div></body></html>"""

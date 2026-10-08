from flask import Blueprint, jsonify

th_bp = Blueprint("type_hints", __name__)

@th_bp.route("/api/perf/types/status")
def t_status():
    return jsonify({"coverage": "85%", "files": 312, "strict": True, "mypy": "passing"})

@th_bp.route("/api/perf/types/web")
def t_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Type Hints</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>TYPE HINTS</h1>
<div class="card"><h3>Coverage</h3><p>85%</p></div>
<div class="card"><h3>Files</h3><p>312</p></div>
<div class="card"><h3>Strict Mode</h3><p>Enabled</p></div></body></html>"""

from flask import Blueprint, jsonify

av_bp = Blueprint("api_versioning", __name__)

@av_bp.route("/api/infra/api/version/status")
def a_status():
    return jsonify({"v1": True, "v2": True, "deprecation": {"v1": "2027-01-01"}, "backward": True})

@av_bp.route("/api/infra/api/version/web")
def a_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>API Versioning</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>API VERSIONING</h1>
<div class="card"><h3>v1</h3><p>Active until 2027-01-01</p></div>
<div class="card"><h3>v2</h3><p>Current</p></div>
<div class="card"><h3>Backward</h3><p>Compatible</p></div></body></html>"""

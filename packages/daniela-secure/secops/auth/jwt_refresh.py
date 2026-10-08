from flask import Blueprint, jsonify

jwt_bp = Blueprint("jwt_refresh", __name__)

@jwt_bp.route("/api/secure/auth/status")
def j_status():
    return jsonify({"access_ttl": 3600, "refresh_ttl": 86400, "algorithm": "HS256", "rotation": True})

@jwt_bp.route("/api/secure/auth/web")
def j_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>JWT Refresh</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>JWT REFRESH</h1>
<div class="card"><h3>Access TTL</h3><p>1 hour</p></div>
<div class="card"><h3>Refresh TTL</h3><p>24 hours</p></div>
<div class="card"><h3>Rotation</h3><p>Enabled</p></div></body></html>"""

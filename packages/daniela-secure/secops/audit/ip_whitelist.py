from flask import Blueprint, jsonify

ip_bp = Blueprint("ip_whitelist", __name__)

@ip_bp.route("/api/secure/whitelist/status")
def i_status():
    return jsonify({"enabled": True, "internal": ["127.0.0.1", "192.168.1.0/24"], "external": "denied"})

@ip_bp.route("/api/secure/whitelist/web")
def i_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>IP Whitelist</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>IP WHITELIST</h1>
<div class="card"><h3>Internal</h3><p>192.168.1.0/24</p></div>
<div class="card"><h3>External</h3><p>Denied</p></div>
<div class="card"><h3>Status</h3><p>Active</p></div></body></html>"""

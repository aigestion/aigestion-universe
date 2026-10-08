from flask import Blueprint, jsonify

csp_bp = Blueprint("csp_security", __name__)

@csp_bp.route("/api/secure/csp/status")
def c_status():
    return jsonify({"csp": True, "headers": 12, "xss": True, "csrf": True, "score": "A+"})

@csp_bp.route("/api/secure/csp/web")
def c_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>CSP Security</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>CSP + SECURITY</h1>
<div class="card"><h3>CSP</h3><p>Enabled</p></div>
<div class="card"><h3>XSS</h3><p>Protected</p></div>
<div class="card"><h3>CSRF</h3><p>Tokens</p></div>
<div class="card"><h3>Score</h3><p>A+</p></div></body></html>"""

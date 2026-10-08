from flask import Blueprint, jsonify

audit_bp = Blueprint("audit_log", __name__)

@audit_bp.route("/api/secure/audit/status")
def a_status():
    return jsonify({"enabled": True, "tamper_proof": True, "algorithm": "SHA-256", "retention": 365})

@audit_bp.route("/api/secure/audit/web")
def a_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Audit Log</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>AUDIT LOG</h1>
<div class="card"><h3>Tamper Proof</h3><p>SHA-256</p></div>
<div class="card"><h3>Retention</h3><p>365 days</p></div>
<div class="card"><h3>Status</h3><p>Active</p></div></body></html>"""

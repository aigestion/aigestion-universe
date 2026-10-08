from flask import Blueprint, jsonify

auto_responder_bp = Blueprint("email_auto_responder", __name__)
_rules = [{"trigger": "out of office", "response": "I'm currently unavailable. Will respond when back.", "active": True}]

@auto_responder_bp.route("/api/hermes/automation/auto-responder/status")
def ar_status():
    return jsonify({"rules": _rules})

@auto_responder_bp.route("/api/hermes/automation/auto-responder/web")
def ar_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Email Auto-Responder</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.rule{background:#111;border:1px solid #333;border-radius:8px;padding:10px;margin:5px 0}
</style></head><body><h1>EMAIL AUTO-RESPONDER</h1><div id="rules"></div>
<script>fetch('/api/hermes/automation/auto-responder/status').then(r=>r.json()).then(d=>{document.getElementById('rules').innerHTML=d.rules.map(r=>'<div class="rule"><strong>Trigger:</strong> '+r.trigger+'<br><strong>Response:</strong> '+r.response+'</div>').join('')})</script></body></html>"""

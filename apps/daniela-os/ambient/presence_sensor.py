import time

from flask import Blueprint, jsonify, request

presence_bp = Blueprint("presence", __name__)
_state = {"present": True, "device": "pc", "last_seen": time.time(), "auto": True}


@presence_bp.route("/api/ambient/presence/status")
def pr_status():
    return jsonify(_state)


@presence_bp.route("/api/ambient/presence/ping", methods=["POST"])
def pr_ping():
    data = request.json or {}
    _state["device"] = data.get("device", "pc")
    _state["last_seen"] = time.time()
    _state["present"] = True
    return jsonify({"ok": True})


@presence_bp.route("/api/ambient/presence/web")
def pr_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Presence Sensor</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.indicator{width:200px;height:200px;border-radius:50%;border:4px solid #00f0ff;display:flex;align-items:center;justify-content:center;font-size:60px;transition:all .5s}
.present{background:#00ff8822;border-color:#00ff88;box-shadow:0 0 60px #00ff8844}
.absent{background:#ff006622;border-color:#ff0066;box-shadow:0 0 60px #ff006644}
</style></head><body>
<div class="indicator" id="ind">📍</div>
<script>setInterval(()=>{fetch('/api/ambient/presence/status').then(r=>r.json()).then(d=>{const i=document.getElementById('ind');i.className='indicator '+(d.present?'present':'absent');i.textContent=d.present?'✅':'❌'})},5000)</script>
</body></html>"""

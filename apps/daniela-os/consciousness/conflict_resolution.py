import time

from flask import Blueprint, jsonify, request

conflict_bp = Blueprint("conflict_resolution", __name__)
_log = []


@conflict_bp.route("/api/consciousness/conflict/log")
def c_log():
    return jsonify({"log": _log[-20:]})


@conflict_bp.route("/api/consciousness/conflict/resolve", methods=["POST"])
def c_resolve():
    data = request.json or {}
    entry = {
        "key": data.get("key", ""),
        "pc_value": data.get("pc_value"),
        "phone_value": data.get("phone_value"),
        "resolution": data.get("phone_value"),
        "strategy": "last-write-wins",
        "time": time.time(),
    }
    _log.append(entry)
    return jsonify({"ok": True, "resolved": entry["resolution"]})


@conflict_bp.route("/api/consciousness/conflict/web")
def c_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Conflict Resolution</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.log-entry{background:#111;border:1px solid #00f0ff33;border-radius:8px;padding:15px;margin:10px 0}
.resolved{color:#00ff88;font-weight:bold}
</style></head><body>
<h1>CONFLICT RESOLUTION LOG</h1>
<div id="log"></div>
<script>setInterval(()=>{fetch('/api/consciousness/conflict/log').then(r=>r.json()).then(d=>{document.getElementById('log').innerHTML=d.log.map(e=>'<div class="log-entry"><p>Key: '+e.key+'</p><p>PC: '+e.pc_value+' vs Phone: '+e.phone_value+'</p><p class="resolved">Resolved: '+e.resolution+' ('+e.strategy+')</p></div>').reverse().join('')})},5000)
</script></body></html>"""

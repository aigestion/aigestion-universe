import time

from flask import Blueprint, jsonify, request

heartbeat_bp = Blueprint("heartbeat", __name__)
_state = {"active": True, "bpm": 72, "pattern": "normal", "history": []}


@heartbeat_bp.route("/api/ambient/heartbeat/status")
def hb_status():
    return jsonify(_state)


@heartbeat_bp.route("/api/ambient/heartbeat/set", methods=["POST"])
def hb_set():
    data = request.json or {}
    _state["bpm"] = data.get("bpm", 72)
    _state["pattern"] = data.get("pattern", "normal")
    return jsonify({"ok": True})


@heartbeat_bp.route("/api/ambient/heartbeat/pulse")
def hb_pulse():
    _state["history"].append(time.time())
    if len(_state["history"]) > 100:
        _state["history"] = _state["history"][-100:]
    interval = 60.0 / max(_state["bpm"], 1)
    return jsonify({"bpm": _state["bpm"], "interval": interval, "pattern": _state["pattern"]})


@heartbeat_bp.route("/api/ambient/heartbeat/web")
def hb_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Heartbeat</title>
<style>body{margin:0;background:#0a0a0f;display:flex;justify-content:center;align-items:center;height:100vh;font-family:monospace;color:#00f0ff}
.heart{width:200px;height:200px;border-radius:50%;background:radial-gradient(circle,#ff0066,#cc0044);box-shadow:0 0 60px #ff0066;animation:beat 1s infinite}
@keyframes beat{0%,100%{transform:scale(1)}15%{transform:scale(1.15)}30%{transform:scale(1)}50%{transform:scale(1.1)}75%{transform:scale(1)}}
.info{position:fixed;bottom:40px;text-align:center;width:100%}
</style></head><body>
<div class="heart" id="heart"></div>
<div class="info"><h2>DANIELA HEARTBEAT</h2><p id="bpm">BPM: 72</p><p id="status">Status: Alive</p></div>
<script>setInterval(()=>{fetch('/api/ambient/heartbeat/pulse').then(r=>r.json()).then(d=>{document.getElementById('bpm').textContent='BPM: '+d.bpm;document.getElementById('heart').style.animationDuration=(60/d.bpm)+'s'})},5000)</script>
</body></html>"""

import time

from flask import Blueprint, jsonify, request

breathing_bp = Blueprint("breathing", __name__)
_state = {"active": True, "mode": "calm", "color": "#00f0ff", "phase": "inhale", "cycle_ms": 4000}

PHASES = {
    "calm": {"colors": ["#00f0ff", "#0088cc"], "cycle": 4000},
    "urgent": {"colors": ["#ff0066", "#ff3300"], "cycle": 1500},
    "sleep": {"colors": ["#1a0033", "#330066"], "cycle": 6000},
    "focus": {"colors": ["#00ff88", "#00cc66"], "cycle": 3000},
}


@breathing_bp.route("/api/ambient/breathing/status")
def br_status():
    return jsonify(_state)


@breathing_bp.route("/api/ambient/breathing/set", methods=["POST"])
def br_set():
    data = request.json or {}
    mode = data.get("mode", "calm")
    if mode in PHASES:
        _state["mode"] = mode
        _state["color"] = PHASES[mode]["colors"][0]
        _state["cycle_ms"] = PHASES[mode]["cycle"]
    return jsonify({"ok": True})


@breathing_bp.route("/api/ambient/breathing/pulse")
def br_pulse():
    t = time.time() * 1000
    cycle = _state["cycle_ms"]
    progress = (t % cycle) / cycle
    if progress < 0.4:
        phase, intensity = "inhale", progress / 0.4
    elif progress < 0.5:
        phase, intensity = "hold", 1.0
    elif progress < 0.9:
        phase, intensity = "exhale", 1.0 - (progress - 0.5) / 0.4
    else:
        phase, intensity = "rest", 0.0
    _state["phase"] = phase
    return jsonify({"phase": phase, "intensity": intensity, "color": _state["color"]})


@breathing_bp.route("/api/ambient/breathing/web")
def br_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Breathing Light</title>
<style>body{margin:0;background:#0a0a0f;display:flex;justify-content:center;align-items:center;height:100vh;font-family:monospace;color:#00f0ff}
.orb{width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,#00f0ff,#001a33);transition:all 2s ease-in-out}
</style></head><body>
<div class="orb" id="orb"></div>
<script>setInterval(()=>{fetch('/api/ambient/breathing/pulse').then(r=>r.json()).then(d=>{const o=document.getElementById('orb');const s=60+d.intensity*140;o.style.width=s+'px';o.style.height=s+'px';o.style.background=`radial-gradient(circle,${d.color},${d.color}22)`;o.style.boxShadow=`0 0 ${d.intensity*80}px ${d.color}`})},200)</script>
</body></html>"""

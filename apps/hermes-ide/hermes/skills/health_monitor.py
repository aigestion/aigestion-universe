from flask import Blueprint, jsonify, request

health_bp = Blueprint("health_monitor", __name__)

SKILL = {"name": "Health Monitor", "description": "Track activity, sleep, stress levels"}

_state = {"steps": 8500, "sleep_hours": 7.5, "stress_level": "medium", "water_glasses": 5, "mood": "good"}

@health_bp.route("/api/hermes/skills/health/status")
def h_status():
    return jsonify(_state)

@health_bp.route("/api/hermes/skills/health/update", methods=["POST"])
def h_update():
    data = request.json or {}
    for k, v in data.items():
        if k in _state:
            _state[k] = v
    return jsonify({"ok": True})

@health_bp.route("/api/hermes/skills/health/web")
def h_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Health Monitor</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.ring{width:150px;height:150px;border-radius:50%;border:8px solid #333;display:flex;align-items:center;justify-content:center;margin:0 auto}
.ring .val{font-size:30px;color:#00ff88}
.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:20px}
.stat{background:#111;border:1px solid #333;border-radius:8px;padding:15px;text-align:center}
.stat .num{font-size:24px;color:#00ff88}
</style></head><body>
<h1 style="text-align:center">HEALTH</h1>
<div class="ring"><div class="val" id="steps">8500</div></div>
<p style="text-align:center">Steps today</p>
<div class="stats">
<div class="stat"><div class="num" id="sleep">7.5h</div><p>Sleep</p></div>
<div class="stat"><div class="num" id="stress">Medium</div><p>Stress</p></div>
<div class="stat"><div class="num" id="water">5</div><p>Water glasses</p></div>
<div class="stat"><div class="num" id="mood">Good</div><p>Mood</p></div>
</div>
<script>fetch('/api/hermes/skills/health/status').then(r=>r.json()).then(d=>{document.getElementById('steps').textContent=d.steps;document.getElementById('sleep').textContent=d.sleep_hours+'h';document.getElementById('stress').textContent=d.stress_level;document.getElementById('water').textContent=d.water_glasses;document.getElementById('mood').textContent=d.mood})</script></body></html>"""

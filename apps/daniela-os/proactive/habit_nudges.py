import time

from flask import Blueprint, jsonify, request

nudges_bp = Blueprint("habit_nudges", __name__)
_habits = [
    {
        "id": 1,
        "name": "Beber agua",
        "frequency": "every_2h",
        "last": time.time() - 7200,
        "active": True,
    },
    {
        "id": 2,
        "name": "Descansar ojos",
        "frequency": "every_30m",
        "last": time.time() - 1800,
        "active": True,
    },
    {
        "id": 3,
        "name": "Levantarse",
        "frequency": "every_1h",
        "last": time.time() - 3600,
        "active": True,
    },
]


@nudges_bp.route("/api/proactive/nudges/status")
def n_status():
    now = time.time()
    for h in _habits:
        if h["active"]:
            if "2h" in h["frequency"]:
                h["due"] = now - h["last"] > 7200
            elif "30m" in h["frequency"]:
                h["due"] = now - h["last"] > 1800
            elif "1h" in h["frequency"]:
                h["due"] = now - h["last"] > 3600
    return jsonify({"habits": _habits})


@nudges_bp.route("/api/proactive/nudges/acknowledge", methods=["POST"])
def n_ack():
    data = request.json or {}
    for h in _habits:
        if h["id"] == data.get("id"):
            h["last"] = time.time()
    return jsonify({"ok": True})


@nudges_bp.route("/api/proactive/nudges/web")
def n_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Habit Nudges</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.habit{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;margin:10px 0;display:flex;justify-content:space-between;align-items:center}
.habit.due{border-color:#ff8800;background:#ff880011}
.ack-btn{background:#00ff8822;border:1px solid #00ff88;color:#00ff88;padding:8px 16px;border-radius:6px;cursor:pointer}
</style></head><body>
<h1>HABIT NUDGES</h1>
<div id="list"></div>
<script>function load(){fetch('/api/proactive/nudges/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.habits.map(h=>'<div class="habit '+(h.due?'due':'')+'"><div><h3>'+h.name+'</h3><p>Frequency: '+h.frequency+'</p></div>'+(h.due?'<button class="ack-btn" onclick="ack('+h.id+')">Done!</button>':'<p>OK</p>')+'</div>').join('')})}
function ack(id){fetch('/api/proactive/nudges/acknowledge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})}).then(()=>load())}
load();setInterval(load,30000)
</script></body></html>"""

import time

from flask import Blueprint, jsonify, request

memory_lane_bp = Blueprint("memory_lane", __name__)
_memories = [
    {
        "id": 1,
        "date": "2026-01-15",
        "title": "Primer dia de Daniela OS",
        "mood": "excited",
        "desc": "El inicio de todo",
    },
    {
        "id": 2,
        "date": "2026-03-20",
        "title": "Video 30s completado",
        "mood": "happy",
        "desc": "Logro importante",
    },
    {
        "id": 3,
        "date": "2026-06-10",
        "title": "62 sistemas activos",
        "mood": "proud",
        "desc": "El ecosistema crece",
    },
]


@memory_lane_bp.route("/api/emotional/memory-lane/status")
def ml_status():
    return jsonify({"memories": _memories})


@memory_lane_bp.route("/api/emotional/memory-lane/add", methods=["POST"])
def ml_add():
    data = request.json or {}
    _memories.append(
        {
            "id": len(_memories) + 1,
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "title": data.get("title", "New memory"),
            "mood": data.get("mood", "happy"),
            "desc": data.get("desc", ""),
        }
    )
    return jsonify({"ok": True})


@memory_lane_bp.route("/api/emotional/memory-lane/web")
def ml_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Memory Lane</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.timeline{max-width:600px;margin:0 auto}
.memory{background:#111;border-left:3px solid #00f0ff;border-radius:0 12px 12px 0;padding:20px;margin:15px 0;position:relative}
.memory::before{content:'';position:absolute;left:-9px;top:25px;width:12px;height:12px;border-radius:50%;background:#00f0ff}
.memory h3{margin-top:0}
.memory .date{color:#666;font-size:12px}
</style></head><body>
<h1 style="text-align:center">MEMORY LANE</h1>
<div class="timeline" id="timeline"></div>
<script>fetch('/api/emotional/memory-lane/status').then(r=>r.json()).then(d=>{document.getElementById('timeline').innerHTML=d.memories.map(m=>'<div class="memory"><div class="date">'+m.date+'</div><h3>'+m.title+'</h3><p>'+m.desc+'</p></div>').join('')})</script>
</body></html>"""

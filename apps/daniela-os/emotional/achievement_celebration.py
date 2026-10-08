from flask import Blueprint, jsonify, request

celebration_bp = Blueprint("achievement_celebration", __name__)
_achievements = [
    {
        "id": 1,
        "name": "Primera Conexion",
        "desc": "Daniela se conecto por primera vez",
        "date": "2026-01-15",
        "unlocked": True,
    },
    {
        "id": 2,
        "name": "10 Sistemas",
        "desc": "10 sistemas activos",
        "date": "2026-03-01",
        "unlocked": True,
    },
    {
        "id": 3,
        "name": "50 Sistemas",
        "desc": "50 sistemas activos",
        "date": "2026-06-01",
        "unlocked": True,
    },
]


@celebration_bp.route("/api/emotional/celebration/status")
def c_status():
    return jsonify({"achievements": _achievements})


@celebration_bp.route("/api/emotional/celebration/unlock", methods=["POST"])
def c_unlock():
    data = request.json or {}
    for a in _achievements:
        if a["id"] == data.get("id"):
            a["unlocked"] = True
    return jsonify({"ok": True})


@celebration_bp.route("/api/emotional/celebration/web")
def c_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Achievement Celebration</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.achievements{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:800px;margin:0 auto}
.ach{background:#111;border:2px solid #333;border-radius:12px;padding:20px;text-align:center;transition:all .3s}
.ach.unlocked{border-color:#00ff88;background:#00ff8811}
.ach.locked{opacity:.5}
.ach .icon{font-size:40px;margin:10px 0}
</style></head><body>
<h1 style="text-align:center">ACHIEVEMENTS</h1>
<div class="achievements" id="list"></div>
<script>fetch('/api/emotional/celebration/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.achievements.map(a=>'<div class="ach '+(a.unlocked?'unlocked':'locked')+'"><div class="icon">'+(a.unlocked?'🏆':'🔒')+'</div><h3>'+a.name+'</h3><p>'+a.desc+'</p><p style="font-size:11px;color:#666">'+a.date+'</p></div>').join('')})</script>
</body></html>"""

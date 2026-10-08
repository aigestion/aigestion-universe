from flask import Blueprint, jsonify

growth_bp = Blueprint("growth_tracking", __name__)
_milestones = [
    {"id": 1, "title": "Primer commit", "date": "2026-01-15", "category": "code", "impact": 10},
    {
        "id": 2,
        "title": "1000 lineas de codigo",
        "date": "2026-02-20",
        "category": "code",
        "impact": 25,
    },
    {
        "id": 3,
        "title": "62 sistemas activos",
        "date": "2026-06-10",
        "category": "system",
        "impact": 50,
    },
]


@growth_bp.route("/api/emotional/growth/status")
def g_status():
    return jsonify({"milestones": _milestones})


@growth_bp.route("/api/emotional/growth/web")
def g_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Growth Tracking</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.milestone{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;margin:10px 0;display:flex;gap:20px;align-items:center}
.milestone .impact{font-size:30px;color:#00ff88;font-weight:bold;width:60px;text-align:center}
</style></head><body>
<h1>GROWTH TRACKING</h1>
<div id="list"></div>
<script>fetch('/api/emotional/growth/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.milestones.map(m=>'<div class="milestone"><div class="impact">+'+m.impact+'</div><div><h3>'+m.title+'</h3><p>'+m.date+' | '+m.category+'</p></div></div>').join('')})</script>
</body></html>"""

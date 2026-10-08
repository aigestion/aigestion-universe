from flask import Blueprint, jsonify

temporal_bp = Blueprint("temporal_memory", __name__)
_patterns = [
    {"pattern": "Lunes 9am: Reunion", "confidence": 0.95, "type": "meeting"},
    {"pattern": "Viernes 6pm: Gym", "confidence": 0.88, "type": "activity"},
    {"pattern": "Domingo 10am: Familia", "confidence": 0.72, "type": "social"}
]

@temporal_bp.route("/api/hermes/memory/temporal/status")
def t_status():
    return jsonify({"patterns": _patterns})

@temporal_bp.route("/api/hermes/memory/temporal/web")
def t_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Temporal Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.pattern{background:#111;padding:10px;margin:5px 0;border-radius:8px}
.bar{height:6px;background:#222;border-radius:3px;margin-top:5px}
.fill{height:100%;background:#00ff88;border-radius:3px}
</style></head><body><h1>TEMPORAL MEMORY</h1><div id="patterns"></div>
<script>fetch('/api/hermes/memory/temporal/status').then(r=>r.json()).then(d=>{document.getElementById('patterns').innerHTML=d.patterns.map(p=>'<div class="pattern"><strong>'+p.pattern+'</strong><div class="bar"><div class="fill" style="width:'+(p.confidence*100)+'%"></div></div></div>').join('')})</script></body></html>"""

from flask import Blueprint, jsonify

pattern_bp = Blueprint("pattern_learning", __name__)
_patterns = [
    {"pattern": "Lunes 9am: Reunion con Pedro", "confidence": 0.95, "type": "meeting"},
    {"pattern": "Viernes 6pm: Gym", "confidence": 0.88, "type": "activity"},
    {"pattern": "Domingo 10am: Familia", "confidence": 0.72, "type": "social"},
]


@pattern_bp.route("/api/proactive/patterns/status")
def p_status():
    return jsonify({"patterns": _patterns})


@pattern_bp.route("/api/proactive/patterns/web")
def p_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Pattern Learning</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.pattern{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;margin:10px 0}
.confidence{height:8px;background:#222;border-radius:4px;margin-top:10px}
.conf-fill{height:100%;background:#00ff88;border-radius:4px}
</style></head><body>
<h1>LEARNED PATTERNS</h1>
<div id="list"></div>
<script>fetch('/api/proactive/patterns/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.patterns.map(p=>'<div class="pattern"><h3>'+p.pattern+'</h3><p>Type: '+p.type+' | Confidence: '+(p.confidence*100).toFixed(0)+'%</p><div class="confidence"><div class="conf-fill" style="width:'+(p.confidence*100)+'%"></div></div></div>').join('')})</script>
</body></html>"""

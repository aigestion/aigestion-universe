from flask import Blueprint, jsonify

self_improvement_bp = Blueprint("self_improvement", __name__)

_improvements = [
    {"area": "Response time", "before": "2.5s", "after": "1.8s", "improvement": "28%"},
    {"area": "Memory recall", "before": "85%", "after": "92%", "improvement": "8%"},
    {"area": "Task accuracy", "before": "88%", "after": "94%", "improvement": "7%"}
]

@self_improvement_bp.route("/api/hermes/advanced/improvement/status")
def si_status():
    return jsonify({"improvements": _improvements})

@self_improvement_bp.route("/api/hermes/advanced/improvement/web")
def si_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Self Improvement</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.improve{background:#111;border:1px solid #00ff88;border-radius:8px;padding:15px;margin:10px 0}
.improve .val{color:#00ff88;font-weight:bold}
</style></head><body><h1>SELF IMPROVEMENT</h1><div id="improvements"></div>
<script>fetch('/api/hermes/advanced/improvement/status').then(r=>r.json()).then(d=>{document.getElementById('improvements').innerHTML=d.improvements.map(i=>'<div class="improve"><h3>'+i.area+'</h3><p>Before: '+i.before+' -> After: <span class="val">'+i.after+'</span></p><p>Improvement: <span class="val">'+i.improvement+'</span></p></div>').join('')})</script></body></html>"""

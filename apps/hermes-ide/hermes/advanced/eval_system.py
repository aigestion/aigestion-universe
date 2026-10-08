from flask import Blueprint, jsonify

eval_system_bp = Blueprint("eval_system", __name__)

_evals = [
    {"name": "Response Quality", "score": 92, "trend": "up"},
    {"name": "Task Completion", "score": 88, "trend": "stable"},
    {"name": "Memory Accuracy", "score": 85, "trend": "up"}
]

@eval_system_bp.route("/api/hermes/advanced/eval/status")
def e_status():
    return jsonify({"evals": _evals, "avg_score": sum(e["score"] for e in _evals) // len(_evals)})

@eval_system_bp.route("/api/hermes/advanced/eval/web")
def e_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Eval System</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.eval{background:#111;border-radius:8px;padding:15px;margin:10px 0}
.bar{height:8px;background:#222;border-radius:4px;margin-top:5px}
.fill{height:100%;background:#00ff88;border-radius:4px}
.up{color:#00ff88} .down{color:#ff0066} .stable{color:#ff8800}
</style></head><body><h1>EVAL SYSTEM</h1>
<p>Average Score: <span id="avg">--</span></p><div id="evals"></div>
<script>fetch('/api/hermes/advanced/eval/status').then(r=>r.json()).then(d=>{document.getElementById('avg').textContent=d.avg_score+'%';document.getElementById('evals').innerHTML=d.evals.map(e=>'<div class="eval"><h3>'+e.name+' - '+e.score+'% <span class="'+e.trend+'">'+e.trend+'</span></h3><div class="bar"><div class="fill" style="width:'+e.score+'%"></div></div></div>').join('')})</script></body></html>"""

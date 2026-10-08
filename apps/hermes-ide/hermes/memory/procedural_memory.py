from flask import Blueprint, jsonify, request

procedural_bp = Blueprint("procedural_memory", __name__)
_procedures = [
    {"name": "Deploy to GitHub", "steps": ["git add .", "git commit -m 'msg'", "git push origin branch"], "category": "git"},
    {"name": "Start Daniela", "steps": ["cd daniela-omnipresente", "python server.py"], "category": "system"},
    {"name": "Run tests", "steps": ["python -m pytest", "Check coverage"], "category": "testing"}
]

@procedural_bp.route("/api/hermes/memory/procedural/status")
def p_status():
    return jsonify({"procedures": _procedures})

@procedural_bp.route("/api/hermes/memory/procedural/add", methods=["POST"])
def p_add():
    data = request.json or {}
    _procedures.append({"name": data.get("name",""), "steps": data.get("steps",[]), "category": data.get("category","general")})
    return jsonify({"ok": True})

@procedural_bp.route("/api/hermes/memory/procedural/web")
def p_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Procedural Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.proc{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0}
.proc h3{margin-top:0}
.step{background:#00f0ff11;padding:4px 8px;margin:3px 0;border-radius:4px;font-family:monospace;font-size:12px}
</style></head><body><h1>PROCEDURAL MEMORY</h1><div id="procs"></div>
<script>fetch('/api/hermes/memory/procedural/status').then(r=>r.json()).then(d=>{document.getElementById('procs').innerHTML=d.procedures.map(p=>'<div class="proc"><h3>'+p.name+'</h3><small>'+p.category+'</small>'+p.steps.map(s=>'<div class="step">'+s+'</div>').join('')+'</div>').join('')})</script></body></html>"""

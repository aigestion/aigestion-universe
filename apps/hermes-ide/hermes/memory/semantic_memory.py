from flask import Blueprint, jsonify, request

semantic_bp = Blueprint("semantic_memory", __name__)
_concepts = [
    {"concept": "Python", "relations": ["language", "programming", "backend"], "strength": 0.9},
    {"concept": "Daniela", "relations": ["AI", "assistant", "ecosystem"], "strength": 1.0},
    {"concept": "Hermes", "relations": ["AI", "agent", "personal"], "strength": 1.0}
]

@semantic_bp.route("/api/hermes/memory/semantic/status")
def s_status():
    return jsonify({"concepts": _concepts})

@semantic_bp.route("/api/hermes/memory/semantic/add", methods=["POST"])
def s_add():
    data = request.json or {}
    _concepts.append({"concept": data.get("concept",""), "relations": data.get("relations",[]), "strength": data.get("strength", 0.5)})
    return jsonify({"ok": True})

@semantic_bp.route("/api/hermes/memory/semantic/web")
def s_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Semantic Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.concept{background:#111;border:1px solid #333;border-radius:8px;padding:10px;margin:5px 0}
.relation{display:inline-block;background:#00f0ff11;padding:2px 8px;border-radius:10px;font-size:11px;margin:2px}
</style></head><body><h1>SEMANTIC MEMORY</h1><div id="concepts"></div>
<script>fetch('/api/hermes/memory/semantic/status').then(r=>r.json()).then(d=>{document.getElementById('concepts').innerHTML=d.concepts.map(c=>'<div class="concept"><h3>'+c.concept+'</h3>'+c.relations.map(r=>'<span class="relation">'+r+'</span>').join('')+'</div>').join('')})</script></body></html>"""

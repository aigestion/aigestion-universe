import time

from flask import Blueprint, jsonify, request

emotional_mem_bp = Blueprint("emotional_memory", __name__)
_memories = [
    {"context": "First deployment", "emotion": "excited", "intensity": 0.9, "time": time.time()-86400},
    {"context": "Bug fixed", "emotion": "relieved", "intensity": 0.7, "time": time.time()-3600}
]

@emotional_mem_bp.route("/api/hermes/memory/emotional/status")
def em_status():
    return jsonify({"memories": _memories})

@emotional_mem_bp.route("/api/hermes/memory/emotional/add", methods=["POST"])
def em_add():
    data = request.json or {}
    _memories.append({"context": data.get("context",""), "emotion": data.get("emotion","neutral"), "intensity": data.get("intensity", 0.5), "time": time.time()})
    return jsonify({"ok": True})

@emotional_mem_bp.route("/api/hermes/memory/emotional/web")
def em_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Emotional Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.mem{background:#111;padding:10px;margin:5px 0;border-radius:8px;border-left:3px solid #ff8800}
</style></head><body><h1>EMOTIONAL MEMORY</h1><div id="mems"></div>
<script>fetch('/api/hermes/memory/emotional/status').then(r=>r.json()).then(d=>{document.getElementById('mems').innerHTML=d.memories.map(m=>'<div class="mem"><strong>'+m.emotion+'</strong>: '+m.context+'<br><small>Intensity: '+m.intensity+'</small></div>').join('')})</script></body></html>"""

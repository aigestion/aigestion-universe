import time

from flask import Blueprint, jsonify, request

episodic_bp = Blueprint("episodic_memory", __name__)
_events = [
    {"id": 1, "event": "First conversation with Hermes", "time": time.time() - 86400, "emotion": "excited", "importance": 0.9},
    {"id": 2, "event": "Deployed 114 systems", "time": time.time() - 3600, "emotion": "proud", "importance": 0.95}
]

@episodic_bp.route("/api/hermes/memory/episodic/status")
def e_status():
    return jsonify({"events": _events[-20:], "total": len(_events)})

@episodic_bp.route("/api/hermes/memory/episodic/add", methods=["POST"])
def e_add():
    data = request.json or {}
    _events.append({"id": len(_events)+1, "event": data.get("event",""), "time": time.time(), "emotion": data.get("emotion","neutral"), "importance": data.get("importance", 0.5)})
    return jsonify({"ok": True})

@episodic_bp.route("/api/hermes/memory/episodic/web")
def e_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Episodic Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.event{background:#111;border-left:3px solid #00f0ff;padding:10px;margin:5px 0;border-radius:0 8px 8px 0}
</style></head><body><h1>EPISODIC MEMORY</h1><div id="events"></div>
<script>fetch('/api/hermes/memory/episodic/status').then(r=>r.json()).then(d=>{document.getElementById('events').innerHTML=d.events.reverse().map(e=>'<div class="event"><strong>'+e.event+'</strong><br><small>'+e.emotion+' | importance: '+e.importance+'</small></div>').join('')})</script></body></html>"""

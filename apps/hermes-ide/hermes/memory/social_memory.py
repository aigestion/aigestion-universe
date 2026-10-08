from flask import Blueprint, jsonify, request

social_bp = Blueprint("social_memory", __name__)
_contacts = [
    {"name": "Alejandro", "role": "Owner", "preferences": ["dark mode", "Spanish"], "last_interaction": "today"},
    {"name": "Pedro", "role": "Colleague", "topics": ["project management", "sports"], "last_interaction": "yesterday"}
]

@social_bp.route("/api/hermes/memory/social/status")
def so_status():
    return jsonify({"contacts": _contacts})

@social_bp.route("/api/hermes/memory/social/add", methods=["POST"])
def so_add():
    data = request.json or {}
    _contacts.append({"name": data.get("name",""), "role": data.get("role",""), "preferences": data.get("preferences",[]), "last_interaction": "today"})
    return jsonify({"ok": True})

@social_bp.route("/api/hermes/memory/social/web")
def so_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Social Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.contact{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0}
.pref{display:inline-block;background:#00f0ff11;padding:2px 8px;border-radius:10px;font-size:11px;margin:2px}
</style></head><body><h1>SOCIAL MEMORY</h1><div id="contacts"></div>
<script>fetch('/api/hermes/memory/social/status').then(r=>r.json()).then(d=>{document.getElementById('contacts').innerHTML=d.contacts.map(c=>'<div class="contact"><h3>'+c.name+'</h3><p>'+c.role+'</p>'+(c.preferences||[]).map(p=>'<span class="pref">'+p+'</span>').join('')+'</div>').join('')})</script></body></html>"""

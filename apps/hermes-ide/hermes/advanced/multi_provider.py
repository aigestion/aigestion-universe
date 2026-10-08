from flask import Blueprint, jsonify

multi_provider_bp = Blueprint("multi_provider", __name__)

PROVIDERS = [
    {"name": "Groq", "model": "llama-3.3-70b", "status": "active", "speed": "fast"},
    {"name": "OpenRouter", "model": "multiple", "status": "configured", "speed": "medium"},
    {"name": "Anthropic", "model": "claude-3.5", "status": "available", "speed": "medium"},
    {"name": "Google", "model": "gemini-pro", "status": "available", "speed": "fast"}
]

@multi_provider_bp.route("/api/hermes/advanced/providers/status")
def mp_status():
    return jsonify({"providers": PROVIDERS})

@multi_provider_bp.route("/api/hermes/advanced/providers/web")
def mp_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Multi-Provider</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.provider{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0;display:flex;justify-content:space-between;align-items:center}
.active{border-color:#00ff88} .configured{border-color:#ff8800} .available{border-color:#666}
.badge{padding:3px 8px;border-radius:10px;font-size:10px}
</style></head><body><h1>MULTI-PROVIDER</h1><div id="providers"></div>
<script>fetch('/api/hermes/advanced/providers/status').then(r=>r.json()).then(d=>{document.getElementById('providers').innerHTML=d.providers.map(p=>'<div class="provider '+p.status+'"><div><h3>'+p.name+'</h3><p>'+p.model+'</p></div><span class="badge">'+p.status+'</span></div>').join('')})</script></body></html>"""

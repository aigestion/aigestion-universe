from flask import Blueprint, jsonify, request

spatial_bp = Blueprint("spatial_memory", __name__)
_places = [
    {"name": "Home", "lat": 40.4168, "lon": -3.7038, "context": "Living and working"},
    {"name": "Office", "lat": 40.4170, "lon": -3.7040, "context": "Work meetings"}
]

@spatial_bp.route("/api/hermes/memory/spatial/status")
def sp_status():
    return jsonify({"places": _places})

@spatial_bp.route("/api/hermes/memory/spatial/add", methods=["POST"])
def sp_add():
    data = request.json or {}
    _places.append({"name": data.get("name",""), "lat": data.get("lat",0), "lon": data.get("lon",0), "context": data.get("context","")})
    return jsonify({"ok": True})

@spatial_bp.route("/api/hermes/memory/spatial/web")
def sp_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Spatial Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.place{background:#111;border:1px solid #333;border-radius:8px;padding:10px;margin:5px 0}
</style></head><body><h1>SPATIAL MEMORY</h1><div id="places"></div>
<script>fetch('/api/hermes/memory/spatial/status').then(r=>r.json()).then(d=>{document.getElementById('places').innerHTML=d.places.map(p=>'<div class="place"><h3>'+p.name+'</h3><p>'+p.context+'</p><small>'+p.lat+', '+p.lon+'</small></div>').join('')})</script></body></html>"""

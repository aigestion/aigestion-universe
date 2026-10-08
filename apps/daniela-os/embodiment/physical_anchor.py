from flask import Blueprint, jsonify, request

anchor_bp = Blueprint("physical_anchor", __name__)
_tags = [
    {"id": 1, "name": "Casa", "action": "lights_on", "active": True},
    {"id": 2, "name": "Oficina", "action": "focus_mode", "active": True},
    {"id": 3, "name": "Dormitorio", "action": "sleep_mode", "active": True},
]


@anchor_bp.route("/api/embodiment/anchor/status")
def a_status():
    return jsonify({"tags": _tags})


@anchor_bp.route("/api/embodiment/anchor/trigger", methods=["POST"])
def a_trigger():
    data = request.json or {}
    tag_id = data.get("id")
    for t in _tags:
        if t["id"] == tag_id:
            return jsonify({"ok": True, "action": t["action"]})
    return jsonify({"ok": False})


@anchor_bp.route("/api/embodiment/anchor/web")
def a_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Physical Anchor</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.tags{display:flex;gap:20px;justify-content:center;flex-wrap:wrap}
.tag{background:#111;border:2px solid #00f0ff33;border-radius:12px;padding:30px;text-align:center;cursor:pointer;transition:all .3s;width:150px}
.tag:hover{border-color:#00f0ff;transform:scale(1.05)}
.tag .icon{font-size:40px;margin:10px 0}
</style></head><body>
<h1 style="text-align:center">PHYSICAL ANCHORS</h1>
<div class="tags" id="tags"></div>
<script>fetch('/api/embodiment/anchor/status').then(r=>r.json()).then(d=>{document.getElementById('tags').innerHTML=d.tags.map(t=>'<div class="tag" onclick="trigger('+t.id+')"><div class="icon">🏷</div><h3>'+t.name+'</h3><p>'+t.action+'</p></div>').join('')});
function trigger(id){fetch('/api/embodiment/anchor/trigger',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})}).then(r=>r.json()).then(d=>alert('Triggered: '+d.action))}</script>
</body></html>"""

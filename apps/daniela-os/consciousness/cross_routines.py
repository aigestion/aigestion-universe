from flask import Blueprint, jsonify, request

routines_bp = Blueprint("cross_routines", __name__)
_routines = [
    {
        "id": 1,
        "name": "Buenos Dias",
        "trigger": "07:00",
        "devices": ["pc", "phone"],
        "actions": ["coffee_on", "news", "calendar"],
        "active": True,
    },
    {
        "id": 2,
        "name": "Focus Mode",
        "trigger": "manual",
        "devices": ["pc", "phone"],
        "actions": ["silence_notif", "dark_theme"],
        "active": False,
    },
    {
        "id": 3,
        "name": "Noche",
        "trigger": "23:00",
        "devices": ["pc", "phone"],
        "actions": ["dim_lights", "enable_night"],
        "active": True,
    },
]


@routines_bp.route("/api/consciousness/routines/list")
def r_list():
    return jsonify({"routines": _routines})


@routines_bp.route("/api/consciousness/routines/toggle", methods=["POST"])
def r_toggle():
    data = request.json or {}
    for r in _routines:
        if r["id"] == data.get("id"):
            r["active"] = not r["active"]
    return jsonify({"ok": True})


@routines_bp.route("/api/consciousness/routines/run", methods=["POST"])
def r_run():
    data = request.json or {}
    for r in _routines:
        if r["id"] == data.get("id"):
            return jsonify({"ok": True, "running": r["name"]})
    return jsonify({"ok": False})


@routines_bp.route("/api/consciousness/routines/web")
def r_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Cross-Device Routines</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.routine{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;margin:10px 0;display:flex;justify-content:space-between;align-items:center}
.routine.active{border-color:#00ff88;background:#00ff8811}
.toggle{width:50px;height:26px;border-radius:13px;border:2px solid #333;cursor:pointer;position:relative;transition:all .3s}
.toggle.on{border-color:#00ff88;background:#00ff8833}
.toggle::after{content:'';position:absolute;width:20px;height:20px;border-radius:50%;background:#fff;top:1px;left:1px;transition:all .3s}
.toggle.on::after{left:25px;background:#00ff88}
.run-btn{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:6px 12px;border-radius:6px;cursor:pointer}
</style></head><body>
<h1>CROSS-DEVICE ROUTINES</h1>
<div id="list"></div>
<script>function load(){fetch('/api/consciousness/routines/list').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.routines.map(r=>'<div class="routine '+(r.active?'active':'')+'"><div><h3>'+r.name+'</h3><p>Trigger: '+r.trigger+' | Devices: '+r.devices.join(', ')+'</p><p>Actions: '+r.actions.join(', ')+'</p></div><div><div class="toggle '+(r.active?'on':'')+'" onclick="toggle('+r.id+')"></div><br><button class="run-btn" onclick="run('+r.id+')">Run Now</button></div></div>').join('')})}
function toggle(id){fetch('/api/consciousness/routines/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})}).then(()=>load())}
function run(id){fetch('/api/consciousness/routines/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})}).then(()=>alert('Running!'))}
load()
</script></body></html>"""

from flask import Blueprint, jsonify, request

smart_home_bp = Blueprint("smart_home_hub", __name__)

SKILL = {"name": "Smart Home Hub", "description": "Control IoT devices via Home Assistant"}

devices = [
    {"id": 1, "name": "Living Room Light", "type": "light", "state": "off", "room": "living"},
    {"id": 2, "name": "Bedroom AC", "type": "climate", "state": "22C", "room": "bedroom"},
    {"id": 3, "name": "Front Door Lock", "type": "lock", "state": "locked", "room": "entrance"},
    {"id": 4, "name": "Kitchen Camera", "type": "camera", "state": "recording", "room": "kitchen"}
]

@smart_home_bp.route("/api/hermes/skills/smarthome/status")
def sh_status():
    return jsonify({"devices": devices})

@smart_home_bp.route("/api/hermes/skills/smarthome/toggle", methods=["POST"])
def sh_toggle():
    data = request.json or {}
    device_id = data.get("id")
    for d in devices:
        if d["id"] == device_id:
            d["state"] = "off" if d["state"] == "on" else "on"
    return jsonify({"ok": True})

@smart_home_bp.route("/api/hermes/skills/smarthome/web")
def sh_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Smart Home</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.device{background:#111;border:1px solid #333;border-radius:12px;padding:15px;margin:10px 0;display:flex;justify-content:space-between;align-items:center}
.device.on{border-color:#00ff88}
.toggle{width:50px;height:26px;border-radius:13px;border:2px solid #333;cursor:pointer;position:relative;transition:all .3s}
.toggle.on{border-color:#00ff88;background:#00ff8833}
.toggle::after{content:'';position:absolute;width:20px;height:20px;border-radius:50%;background:#fff;top:1px;left:1px;transition:all .3s}
.toggle.on::after{left:25px;background:#00ff88}
</style></head><body>
<h1>SMART HOME</h1>
<div id="devices"></div>
<script>function load(){fetch('/api/hermes/skills/smarthome/status').then(r=>r.json()).then(d=>{document.getElementById('devices').innerHTML=d.devices.map(dev=>'<div class="device '+(dev.state!=='off'?'on':'')+'"><div><h3>'+dev.name+'</h3><p>'+dev.type+' - '+dev.room+'</p></div><div><p>'+dev.state+'</p><div class="toggle '+(dev.state!=='off'?'on':'')+'" onclick="toggle('+dev.id+')"></div></div></div>').join('')})}
function toggle(id){fetch('/api/hermes/skills/smarthome/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})}).then(()=>load())}
load()</script></body></html>"""

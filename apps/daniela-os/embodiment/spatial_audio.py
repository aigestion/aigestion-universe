from flask import Blueprint, jsonify, request

spatial_bp = Blueprint("spatial_audio", __name__)
_state = {"active": True, "source": {"x": 0, "y": 0}, "mode": "stereo"}


@spatial_bp.route("/api/embodiment/spatial/status")
def s_status():
    return jsonify(_state)


@spatial_bp.route("/api/embodiment/spatial/set", methods=["POST"])
def s_set():
    data = request.json or {}
    _state["source"] = {"x": data.get("x", 0), "y": data.get("y", 0)}
    return jsonify({"ok": True})


@spatial_bp.route("/api/embodiment/spatial/web")
def s_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Spatial Audio</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.room{width:400px;height:400px;border:2px solid #333;border-radius:20px;position:relative}
.source{width:40px;height:40px;background:#00f0ff;border-radius:50%;position:absolute;cursor:move;transition:all .1s;display:flex;align-items:center;justify-content:center;font-size:20px}
.info{position:fixed;bottom:40px;text-align:center;width:100%}
</style></head><body>
<div class="room" id="room"><div class="source" id="source" style="left:180px;top:180px">🔊</div></div>
<div class="info"><p>Drag the sound source around the room</p></div>
<script>const src=document.getElementById('source');const room=document.getElementById('room');
let dragging=false;
src.onmousedown=()=>dragging=true;
document.onmouseup=()=>dragging=false;
document.onmousemove=e=>{if(dragging){const r=room.getBoundingClientRect();const x=Math.max(0,Math.min(360,e.clientX-r.left-20));const y=Math.max(0,Math.min(360,e.clientY-r.top-20));src.style.left=x+'px';src.style.top=y+'px';fetch('/api/embodiment/spatial/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({x:x/200-1,y:y/200-1})})}};
</script></body></html>"""

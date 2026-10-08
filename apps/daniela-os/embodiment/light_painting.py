from flask import Blueprint, jsonify, request

light_painting_bp = Blueprint("light_painting", __name__)
_state = {"active": True, "color": "#00f0ff", "trail": []}


@light_painting_bp.route("/api/embodiment/light/status")
def l_status():
    return jsonify(_state)


@light_painting_bp.route("/api/embodiment/light/set", methods=["POST"])
def l_set():
    data = request.json or {}
    _state["color"] = data.get("color", "#00f0ff")
    return jsonify({"ok": True})


@light_painting_bp.route("/api/embodiment/light/web")
def l_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Light Painting</title>
<style>body{margin:0;background:#0a0a0f;overflow:hidden;font-family:monospace}
canvas{display:block}
.controls{position:fixed;top:20px;left:20px;display:flex;gap:10px}
.color-btn{width:30px;height:30px;border-radius:50%;border:2px solid #333;cursor:pointer}
.clear{padding:8px 16px;background:#111;border:1px solid #333;color:#fff;border-radius:6px;cursor:pointer}
</style></head><body>
<canvas id="canvas"></canvas>
<div class="controls">
<div class="color-btn" style="background:#00f0ff" onclick="setColor('#00f0ff')"></div>
<div class="color-btn" style="background:#ff0066" onclick="setColor('#ff0066')"></div>
<div class="color-btn" style="background:#00ff88" onclick="setColor('#00ff88')"></div>
<div class="color-btn" style="background:#ff8800" onclick="setColor('#ff8800')"></div>
<button class="clear" onclick="clear()">Clear</button>
</div>
<script>const c=document.getElementById('canvas');const ctx=c.getContext('2d');
c.width=window.innerWidth;c.height=window.innerHeight;
let color='#00f0ff',drawing=false,trails=[];
function setColor(c){color=c}
function clear(){trails=[];ctx.clearRect(0,0,c.width,c.height)}
c.onmousedown=()=>drawing=true;
c.onmouseup=()=>drawing=false;
c.onmousemove=e=>{if(drawing){ctx.beginPath();ctx.arc(e.clientX,e.clientY,3,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.shadowBlur=20;ctx.shadowColor=color;ctx.shadowBlur=0}}
</script></body></html>"""

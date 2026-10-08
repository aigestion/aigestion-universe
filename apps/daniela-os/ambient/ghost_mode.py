from flask import Blueprint, jsonify

ghost_bp = Blueprint("ghost", __name__)
_state = {"active": False, "opacity": 0.3, "position": {"x": 0, "y": 0}, "following": False}


@ghost_bp.route("/api/ambient/ghost/status")
def g_status():
    return jsonify(_state)


@ghost_bp.route("/api/ambient/ghost/toggle", methods=["POST"])
def g_toggle():
    _state["active"] = not _state["active"]
    return jsonify({"ok": True, "active": _state["active"]})


@ghost_bp.route("/api/ambient/ghost/web")
def g_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Ghost Mode</title>
<style>body{margin:0;background:#0a0a0f;overflow:hidden;font-family:monospace}
.ghost{position:fixed;width:60px;height:80px;background:radial-gradient(ellipse,#00f0ff22,transparent);border-radius:30px 30px 0 0;filter:blur(2px);pointer-events:none;transition:all .1s}
.ghost::after{content:'👻';font-size:40px;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)}
.info{position:fixed;top:20px;right:20px;background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;color:#00f0ff}
</style></head><body>
<div class="ghost" id="ghost" style="opacity:0.3"></div>
<div class="info"><h3>GHOST MODE</h3><p>La sombra de Daniela sigue tu cursor</p><p><button onclick="toggle()" style="padding:8px 16px;background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;border-radius:6px;cursor:pointer">Toggle</button></p></div>
<script>const ghost=document.getElementById('ghost');let active=false;
document.onmousemove=e=>{if(active){ghost.style.left=(e.clientX-30)+'px';ghost.style.top=(e.clientY-80)+'px'}};
function toggle(){active=!active;ghost.style.opacity=active?0.6:0;fetch('/api/ambient/ghost/toggle',{method:'POST'})}
</script></body></html>"""

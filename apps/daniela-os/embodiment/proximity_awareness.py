import time

from flask import Blueprint, jsonify, request

proximity_bp = Blueprint("proximity_awareness", __name__)
_state = {"near_pc": True, "distance": 0.5, "last_change": time.time(), "auto": True}


@proximity_bp.route("/api/embodiment/proximity/status")
def p_status():
    return jsonify(_state)


@proximity_bp.route("/api/embodiment/proximity/set", methods=["POST"])
def p_set():
    data = request.json or {}
    _state["near_pc"] = data.get("near", True)
    _state["distance"] = data.get("distance", 0.5)
    _state["last_change"] = time.time()
    return jsonify({"ok": True})


@proximity_bp.route("/api/embodiment/proximity/web")
def p_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Proximity Awareness</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.prox{text-align:center}
.radar{width:300px;height:300px;border:2px solid #333;border-radius:50%;margin:20px auto;position:relative;overflow:hidden}
.radar::after{content:'';position:absolute;width:100%;height:100%;border-radius:50%;background:conic-gradient(from 0deg,transparent,#00f0ff22,transparent);animation:spin 3s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.dot{position:absolute;width:12px;height:12px;background:#00ff88;border-radius:50%;top:50%;left:50%;transform:translate(-50%,-50%);transition:all .5s}
</style></head><body>
<div class="prox">
<h2>PROXIMITY</h2>
<div class="radar"><div class="dot" id="dot"></div></div>
<p>Distance: <span id="dist">0.5m</span></p>
<p>Status: <span id="status">Near PC</span></p>
</div>
<script>setInterval(()=>{fetch('/api/embodiment/proximity/status').then(r=>r.json()).then(d=>{document.getElementById('dist').textContent=d.distance+'m';document.getElementById('status').textContent=d.near_pc?'Near PC':'Far away';const dot=document.getElementById('dot');const angle=Math.atan2(d.distance-0.5,0.5)*180/Math.PI;dot.style.transform=`translate(${Math.cos(angle)*d.distance*100}px,${Math.sin(angle)*d.distance*100}px)`})},3000)</script>
</body></html>"""

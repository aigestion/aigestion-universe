import time

from flask import Blueprint, jsonify, request

attention_bp = Blueprint("attention_awareness", __name__)
_state = {"attention": "pc", "last_switch": time.time(), "focus_score": 85, "distractions": 0}


@attention_bp.route("/api/consciousness/attention/status")
def at_status():
    return jsonify(_state)


@attention_bp.route("/api/consciousness/attention/switch", methods=["POST"])
def at_switch():
    data = request.json or {}
    _state["attention"] = data.get("device", "pc")
    _state["last_switch"] = time.time()
    return jsonify({"ok": True})


@attention_bp.route("/api/consciousness/attention/web")
def at_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Attention Awareness</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;gap:40px}
.eye{width:200px;height:100px;border:3px solid #00f0ff;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:all .5s}
.pupil{width:40px;height:40px;background:#00f0ff;border-radius:50%;transition:all .3s}
.info{text-align:center}
.score{font-size:60px;font-weight:bold}
</style></head><body>
<div class="info"><h2>ATTENTION TRACKER</h2><div class="eye"><div class="pupil" id="pupil"></div></div><p>Looking at: <span id="device">PC</span></p><p>Focus Score: <span class="score" id="score">85</span>%</p></div>
<script>setInterval(()=>{fetch('/api/consciousness/attention/status').then(r=>r.json()).then(d=>{document.getElementById('device').textContent=d.attention.toUpperCase();document.getElementById('score').textContent=d.focus_score;const p=document.getElementById('pupil');p.style.transform=d.attention==='phone'?'translateX(30px)':d.attention==='pc'?'translateX(-30px)':'translateY(20px)'})},3000)</script>
</body></html>"""

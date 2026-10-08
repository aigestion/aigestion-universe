from flask import Blueprint, jsonify, request

split_bp = Blueprint("split_consciousness", __name__)
_state = {"pc": {"task": "idle", "load": 15}, "phone": {"task": "idle", "load": 5}, "coherence": 98}


@split_bp.route("/api/consciousness/split/status")
def s_status():
    return jsonify(_state)


@split_bp.route("/api/consciousness/split/assign", methods=["POST"])
def s_assign():
    data = request.json or {}
    device = data.get("device", "pc")
    _state[device]["task"] = data.get("task", "idle")
    _state[device]["load"] = data.get("load", 50)
    return jsonify({"ok": True})


@split_bp.route("/api/consciousness/split/web")
def s_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Split Consciousness</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;gap:40px}
.half{width:300px;background:#111;border:2px solid #00f0ff33;border-radius:20px;padding:30px;text-align:center}
.half .icon{font-size:60px;margin:20px 0}
.coherence{text-align:center;margin-top:40px}
.coherence .score{font-size:80px;color:#00ff88}
.bar{height:12px;background:#222;border-radius:6px;margin:10px 0}
.bar-fill{height:100%;border-radius:6px;transition:width .5s}
</style></head><body>
<div class="half"><div class="icon">🖥</div><h2>PC</h2><p id="pc-task">idle</p><div class="bar"><div class="bar-fill" id="pc-bar" style="width:15%;background:#00f0ff"></div></div></div>
<div class="coherence"><p>COHERENCE</p><div class="score" id="coh">98%</div><p>Two halves, one mind</p></div>
<div class="half"><div class="icon">📱</div><h2>Phone</h2><p id="ph-task">idle</p><div class="bar"><div class="bar-fill" id="ph-bar" style="width:5%;background:#00ff88"></div></div></div>
<script>setInterval(()=>{fetch('/api/consciousness/split/status').then(r=>r.json()).then(d=>{document.getElementById('pc-task').textContent=d.pc.task;document.getElementById('ph-task').textContent=d.phone.task;document.getElementById('pc-bar').style.width=d.pc.load+'%';document.getElementById('ph-bar').style.width=d.phone.load+'%';document.getElementById('coh').textContent=d.coherence+'%'})},3000)</script>
</body></html>"""

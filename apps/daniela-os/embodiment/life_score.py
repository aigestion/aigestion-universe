from flask import Blueprint, jsonify, request

life_score_bp = Blueprint("life_score", __name__)
_state = {
    "health": 85,
    "productivity": 72,
    "social": 60,
    "emotional": 78,
    "total": 74,
    "level": 12,
    "xp": 2450,
    "xp_next": 3000,
}


@life_score_bp.route("/api/embodiment/life/status")
def l_status():
    return jsonify(_state)


@life_score_bp.route("/api/embodiment/life/add-xp", methods=["POST"])
def l_add_xp():
    data = request.json or {}
    amount = data.get("amount", 10)
    _state["xp"] += amount
    if _state["xp"] >= _state["xp_next"]:
        _state["level"] += 1
        _state["xp"] = 0
        _state["xp_next"] = int(_state["xp_next"] * 1.2)
    _state["total"] = (
        _state["health"] + _state["productivity"] + _state["social"] + _state["emotional"]
    ) // 4
    return jsonify({"ok": True})


@life_score_bp.route("/api/embodiment/life/web")
def l_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Life Score</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.game{text-align:center}
.score-ring{width:200px;height:200px;border-radius:50%;border:6px solid #00f0ff;display:flex;align-items:center;justify-content:center;margin:0 auto}
.score-ring .score{font-size:60px;font-weight:bold;color:#00ff88}
.stats{display:flex;gap:20px;margin:30px 0}
.stat{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:15px;width:100px}
.stat .val{font-size:24px;color:#00ff88}
.xp-bar{width:300px;height:12px;background:#222;border-radius:6px;margin:10px auto}
.xp-fill{height:100%;background:#ff8800;border-radius:6px}
</style></head><body>
<div class="game">
<div class="score-ring"><div class="score" id="total">74</div></div>
<p>Level <span id="level">12</span></p>
<div class="xp-bar"><div class="xp-fill" id="xp" style="width:82%"></div></div>
<p><span id="xpn">2450</span> / <span id="xpnx">3000</span> XP</p>
<div class="stats">
<div class="stat"><div class="val" id="health">85</div><p>Health</p></div>
<div class="stat"><div class="val" id="prod">72</div><p>Product</p></div>
<div class="stat"><div class="val" id="social">60</div><p>Social</p></div>
<div class="stat"><div class="val" id="emo">78</div><p>Emotion</p></div>
</div>
<button onclick="addXP()" style="padding:10px 20px;background:#00ff8822;border:1px solid #00ff88;color:#00ff88;border-radius:6px;cursor:pointer">+10 XP</button>
</div>
<script>function load(){fetch('/api/embodiment/life/status').then(r=>r.json()).then(d=>{document.getElementById('total').textContent=d.total;document.getElementById('level').textContent=d.level;document.getElementById('xp').style.width=(d.xp/d.xp_next*100)+'%';document.getElementById('xpn').textContent=d.xp;document.getElementById('xpnx').textContent=d.xp_next;document.getElementById('health').textContent=d.health;document.getElementById('prod').textContent=d.productivity;document.getElementById('social').textContent=d.social;document.getElementById('emo').textContent=d.emotional})}
function addXP(){fetch('/api/embodiment/life/add-xp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount:10})}).then(()=>load())}
load()</script>
</body></html>"""

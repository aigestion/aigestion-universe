from flask import Blueprint, jsonify, request

comm_bp = Blueprint("communication_style", __name__)
_state = {"formality": "casual", "verbosity": "concise", "emoji_usage": "moderate"}

@comm_bp.route("/api/hermes/personality/comm/status")
def co_status():
    return jsonify(_state)

@comm_bp.route("/api/hermes/personality/comm/set", methods=["POST"])
def co_set():
    data = request.json or {}
    for k, v in data.items():
        if k in _state:
            _state[k] = v
    return jsonify({"ok": True})

@comm_bp.route("/api/hermes/personality/comm/web")
def co_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Communication Style</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.opt{background:#111;border:1px solid #333;border-radius:8px;padding:10px;margin:5px 0;cursor:pointer}
.opt.active{border-color:#00ff88}
</style></head><body><h1>COMMUNICATION STYLE</h1>
<h3>Formality</h3>
<div class="opt active" onclick="set('formality','casual')">Casual</div>
<div class="opt" onclick="set('formality','formal')">Formal</div>
<h3>Verbosity</h3>
<div class="opt active" onclick="set('verbosity','concise')">Concise</div>
<div class="opt" onclick="set('verbosity','detailed')">Detailed</div>
<script>function set(k,v){fetch('/api/hermes/personality/comm/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({[k]:v})}).then(()=>location.reload())}</script></body></html>"""

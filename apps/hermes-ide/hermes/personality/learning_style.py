from flask import Blueprint, jsonify, request

learning_bp = Blueprint("learning_style", __name__)
_state = {"style": "visual", "pace": "medium", "preferences": ["examples", "diagrams"]}

@learning_bp.route("/api/hermes/personality/learning/status")
def l_status():
    return jsonify(_state)

@learning_bp.route("/api/hermes/personality/learning/set", methods=["POST"])
def l_set():
    data = request.json or {}
    for k, v in data.items():
        if k in _state:
            _state[k] = v
    return jsonify({"ok": True})

@learning_bp.route("/api/hermes/personality/learning/web")
def l_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Learning Style</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.style{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0;cursor:pointer}
.style.active{border-color:#00ff88;background:#00ff8811}
</style></head><body><h1>LEARNING STYLE</h1>
<div class="style active" onclick="set('visual')">Visual - Diagrams and charts</div>
<div class="style" onclick="set('textual')">Textual - Reading and writing</div>
<div class="style" onclick="set('practical')">Practical - Hands-on examples</div>
<script>function set(s){fetch('/api/hermes/personality/learning/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({style:s})}).then(()=>location.reload())}</script></body></html>"""

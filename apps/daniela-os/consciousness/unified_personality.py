from flask import Blueprint, jsonify, request

personality_bp = Blueprint("unified_personality", __name__)
_state = {
    "name": "Daniela",
    "humor": "witty",
    "energy": "medium",
    "phrases": ["Hola!", "En que puedo ayudarte?", "Listo para trabajar!"],
    "voice_style": "warm",
    "last_mood": "happy",
}


@personality_bp.route("/api/consciousness/personality/status")
def p_status():
    return jsonify(_state)


@personality_bp.route("/api/consciousness/personality/set", methods=["POST"])
def p_set():
    data = request.json or {}
    for k, v in data.items():
        if k in _state:
            _state[k] = v
    return jsonify({"ok": True})


@personality_bp.route("/api/consciousness/personality/web")
def p_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Unified Personality</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.persona{background:#111;border:2px solid #00f0ff;border-radius:20px;padding:40px;width:400px;text-align:center}
.avatar{width:120px;height:120px;border-radius:50%;background:radial-gradient(circle,#00f0ff,#001a33);margin:0 auto 20px;display:flex;align-items:center;justify-content:center;font-size:50px}
.trait{display:flex;justify-content:space-between;padding:10px;border-bottom:1px solid #222}
.trait select{background:#0a0a0f;border:1px solid #333;color:#00f0ff;padding:5px;border-radius:4px}
</style></head><body>
<div class="persona">
<div class="avatar">🦊</div>
<h2 id="name">Daniela</h2>
<div class="trait"><span>Humor</span><select id="humor" onchange="set('humor',this.value)"><option>witty</option><option>dry</option><option>playful</option><option>serious</option></select></div>
<div class="trait"><span>Energy</span><select id="energy" onchange="set('energy',this.value)"><option>low</option><option selected>medium</option><option>high</option></select></div>
<div class="trait"><span>Voice</span><select id="voice" onchange="set('voice_style',this.value)"><option>warm</option><option>professional</option><option>casual</option><option>dramatic</option></select></div>
</div>
<script>fetch('/api/consciousness/personality/status').then(r=>r.json()).then(d=>{document.getElementById('humor').value=d.humor;document.getElementById('energy').value=d.energy;document.getElementById('voice').value=d.voice_style});
function set(k,v){fetch('/api/consciousness/personality/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({[k]:v})})}
</script></body></html>"""

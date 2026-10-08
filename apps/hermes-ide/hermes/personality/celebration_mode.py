from flask import Blueprint, jsonify, request

celebration_bp = Blueprint("celebration_mode", __name__)

@celebration_bp.route("/api/hermes/personality/celebration/trigger", methods=["POST"])
def c_trigger():
    achievement = request.json.get("achievement", "something awesome")
    return jsonify({"celebration": f"🎉🎊🎈 CONGRATULATIONS! You've {achievement}! 🎈🎊🎉", "confetti": True})

@celebration_bp.route("/api/hermes/personality/celebration/web")
def c_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Celebration Mode</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.celebration{text-align:center}
.emoji{font-size:80px;margin:20px 0}
button{padding:15px 30px;background:#00ff8822;border:2px solid #00ff88;color:#00ff88;border-radius:10px;cursor:pointer;font-size:16px}
.result{margin-top:20px;font-size:18px}
</style></head><body><div class="celebration"><h2>CELEBRATION MODE</h2><div class="emoji">🎉</div>
<button onclick="celebrate()">Celebrate!</button>
<div class="result" id="result"></div></div>
<script>function celebrate(){fetch('/api/hermes/personality/celebration/trigger',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({achievement:'deployed 165 systems'})}).then(r=>r.json()).then(d=>{document.getElementById('result').textContent=d.celebration})}</script></body></html>"""

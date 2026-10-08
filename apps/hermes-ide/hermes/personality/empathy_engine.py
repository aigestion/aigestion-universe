from flask import Blueprint, jsonify, request

empathy_bp = Blueprint("empathy_engine", __name__)

RESPONSES = {
    "sad": "I understand you're feeling down. I'm here for you. Would you like to talk about it?",
    "angry": "I can see you're frustrated. Take a deep breath. Let's work through this together.",
    "stressed": "You seem overwhelmed. Let's break this down into smaller steps.",
    "happy": "That's wonderful! I'm glad you're feeling good!",
    "neutral": "How can I help you today?"
}

@empathy_bp.route("/api/hermes/personality/empathy/respond", methods=["POST"])
def e_respond():
    mood = request.json.get("mood", "neutral")
    return jsonify({"response": RESPONSES.get(mood, RESPONSES["neutral"]), "mood": mood})

@empathy_bp.route("/api/hermes/personality/empathy/web")
def e_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Empathy Engine</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.empathy{text-align:center}
.btn{padding:15px 25px;margin:5px;background:#111;border:2px solid #333;border-radius:10px;cursor:pointer;color:#fff;font-size:14px}
.btn:hover{border-color:#00f0ff}
.response{margin-top:20px;padding:20px;background:#111;border-radius:12px;max-width:400px;font-style:italic}
</style></head><body><div class="empathy"><h2>EMPATHY ENGINE</h2>
<p>How are you feeling?</p>
<button class="btn" onclick="respond('sad')">😢 Sad</button>
<button class="btn" onclick="respond('angry')">😠 Angry</button>
<button class="btn" onclick="respond('stressed')">😰 Stressed</button>
<button class="btn" onclick="respond('happy')">😊 Happy</button>
<div class="response" id="response"></div></div>
<script>function respond(mood){fetch('/api/hermes/personality/empathy/respond',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mood})}).then(r=>r.json()).then(d=>{document.getElementById('response').textContent=d.response})}</script></body></html>"""

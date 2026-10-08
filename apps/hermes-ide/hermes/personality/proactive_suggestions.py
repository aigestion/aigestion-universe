from flask import Blueprint, jsonify

proactive_sugg_bp = Blueprint("proactive_suggestions", __name__)

SUGGESTIONS = [
    "You've been coding for 2 hours. How about a break?",
    "Your calendar shows a meeting in 30 minutes.",
    "Consider organizing your downloads folder.",
    "You haven't exercised today. A short walk might help!"
]

@proactive_sugg_bp.route("/api/hermes/personality/suggestions/status")
def ps_status():
    import random
    return jsonify({"suggestion": random.choice(SUGGESTIONS), "all": SUGGESTIONS})

@proactive_sugg_bp.route("/api/hermes/personality/suggestions/web")
def ps_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Proactive Suggestions</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.sugg{text-align:center}
.bulb{font-size:80px;margin:20px 0}
.suggestion{font-size:18px;max-width:400px;margin:20px auto;padding:20px;background:#111;border-radius:12px}
button{padding:15px 30px;background:#ff880022;border:2px solid #ff8800;color:#ff8800;border-radius:10px;cursor:pointer}
</style></head><body><div class="sugg"><h2>PROACTIVE SUGGESTIONS</h2><div class="bulb">💡</div>
<div class="suggestion" id="sugg">Loading...</div>
<button onclick="next()">Next Suggestion</button></div>
<script>function next(){fetch('/api/hermes/personality/suggestions/status').then(r=>r.json()).then(d=>{document.getElementById('sugg').textContent=d.suggestion})}
next()</script></body></html>"""

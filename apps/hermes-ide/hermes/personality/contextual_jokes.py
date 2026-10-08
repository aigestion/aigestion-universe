import random

from flask import Blueprint, jsonify, request

jokes_bp = Blueprint("contextual_jokes", __name__)

CONTEXT_JOKES = {
    "coding": ["Why do programmers prefer dark mode? Light attracts bugs!", "There are 10 types of people..."],
    "meeting": ["Why did the scarecrow win an award? He was outstanding in his field!", "I told my wife she was drawing her eyebrows too high. She looked surprised."],
    "default": ["Why don't scientists trust atoms? Because they make up everything!", "What do you call a fake noodle? An impasta!"]
}

@jokes_bp.route("/api/hermes/personality/jokes/contextual", methods=["POST"])
def cj_get():
    context = request.json.get("context", "default")
    jokes = CONTEXT_JOKES.get(context, CONTEXT_JOKES["default"])
    return jsonify({"joke": random.choice(jokes), "context": context})

@jokes_bp.route("/api/hermes/personality/jokes/web")
def cj_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Contextual Jokes</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.jokes{text-align:center}
.joke{font-size:18px;max-width:400px;margin:20px auto;padding:20px;background:#111;border-radius:12px}
button{padding:10px 20px;margin:5px;background:#111;border:1px solid #333;border-radius:8px;cursor:pointer;color:#fff}
</style></head><body><div class="jokes"><h2>CONTEXTUAL JOKES</h2>
<button onclick="get('coding')">Coding</button>
<button onclick="get('meeting')">Meeting</button>
<button onclick="get('default')">Random</button>
<div class="joke" id="joke">Click a category!</div></div>
<script>function get(ctx){fetch('/api/hermes/personality/jokes/contextual',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({context:ctx})}).then(r=>r.json()).then(d=>{document.getElementById('joke').textContent=d.joke})}</script></body></html>"""

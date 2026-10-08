import random

from flask import Blueprint, jsonify, request

humor_bp = Blueprint("humor_system", __name__)

JOKES = [
    {"joke": "Why do programmers prefer dark mode? Because light attracts bugs!", "style": "nerd"},
    {"joke": "There are 10 types of people: those who understand binary and those who don't.", "style": "nerd"},
    {"joke": "A SQL query walks into a bar, sees two tables and asks... Can I join you?", "style": "nerd"},
    {"joke": "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.", "style": "nerd"},
    {"joke": "Kein Wunder, dass Programmierer dunkel bevorzugen - Licht zieht Bugs an!", "style": "german"}
]

@humor_bp.route("/api/hermes/personality/humor/joke")
def h_joke():
    style = request.args.get("style", "nerd")
    filtered = [j for j in JOKES if j["style"] == style] or JOKES
    return jsonify(random.choice(filtered))

@humor_bp.route("/api/hermes/personality/humor/web")
def h_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Humor System</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.humor{text-align:center}
.joke{font-size:18px;max-width:400px;margin:20px 0;padding:20px;background:#111;border-radius:12px}
button{padding:15px 30px;background:#ff880022;border:2px solid #ff8800;color:#ff8800;border-radius:10px;cursor:pointer;font-size:16px}
</style></head><body><div class="humor"><h2>HUMOR SYSTEM</h2><div class="joke" id="joke">Click for a joke!</div>
<button onclick="joke()">Get Joke</button></div>
<script>function joke(){fetch('/api/hermes/personality/humor/joke').then(r=>r.json()).then(d=>{document.getElementById('joke').textContent=d.joke})}</script></body></html>"""

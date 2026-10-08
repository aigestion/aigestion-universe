from flask import Blueprint, jsonify

language_bp = Blueprint("language_tutor", __name__)

SKILL = {"name": "Language Tutor", "description": "Teach languages via conversation"}

lessons = [
    {"word": "Hola", "translation": "Hello", "language": "es->en", "level": "beginner"},
    {"word": "Gracias", "translation": "Thank you", "language": "es->en", "level": "beginner"},
    {"word": "Buenos dias", "translation": "Good morning", "language": "es->en", "level": "beginner"}
]

@language_bp.route("/api/hermes/skills/language/status")
def l_status():
    return jsonify({"lessons": lessons, "total": len(lessons)})

@language_bp.route("/api/hermes/skills/language/quiz", methods=["POST"])
def l_quiz():
    import random
    lesson = random.choice(lessons)
    return jsonify({"question": f"What does '{lesson['word']}' mean?", "answer": lesson["translation"]})

@language_bp.route("/api/hermes/skills/language/web")
def l_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Language Tutor</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:2px solid #333;border-radius:12px;padding:30px;text-align:center;margin:20px auto;max-width:300px;cursor:pointer;transition:all .3s}
.card:hover{border-color:#00f0ff}
.card .word{font-size:24px;margin:10px 0}
.card .translation{color:#00ff88;display:none}
.show .translation{display:block}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:10px 20px;border-radius:8px;cursor:pointer;margin:5px}
</style></head><body>
<h1 style="text-align:center">LANGUAGE TUTOR</h1>
<div class="card" id="card" onclick="this.classList.toggle('show')"><div class="word" id="word">Hola</div><div class="translation" id="trans">Hello</div></div>
<div style="text-align:center"><button onclick="next()">Next Word</button><button onclick="quiz()">Quiz Me</button></div>
<script>let idx=0;const words=[{w:'Hola',t:'Hello'},{w:'Gracias',t:'Thank you'},{w:'Buenos dias',t:'Good morning'},{w:'Por favor',t:'Please'},{w:'Adios',t:'Goodbye'}];
function next(){idx=(idx+1)%words.length;document.getElementById('word').textContent=words[idx].w;document.getElementById('trans').textContent=words[idx].t;document.getElementById('card').classList.remove('show')}
function quiz(){const w=words[Math.floor(Math.random()*words.length)];alert('What does "'+w.w+'" mean? Click card to reveal answer');document.getElementById('word').textContent=w.w;document.getElementById('trans').textContent=w.t;document.getElementById('card').classList.remove('show')}</script></body></html>"""

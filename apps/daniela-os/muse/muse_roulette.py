import random
from datetime import datetime

from flask import Blueprint, jsonify, request

roulette_bp = Blueprint("muse_roulette", __name__)
_state = {"last_day": "", "prompt": "", "streak": 0, "spins": 0}

PROMPTS = [
    "Escribe sobre una llave que abre algo imposible.",
    "Un personaje que recuerda el futuro.",
    "Diálogo solo con preguntas.",
    "La ciudad donde está prohibido dormir.",
    "Carta de un objeto a su dueño.",
    "El último mensaje de una botella.",
    "Alguien que colecciona silencios.",
    "Una receta que es en realidad un hechizo.",
]


@roulette_bp.route("/api/muse/roulette/spin", methods=["POST"])
def mr_spin():
    today = datetime.now().strftime("%Y-%m-%d")
    data = request.json or {}
    who = data.get("who", "yo")
    if _state["last_day"] != today:
        _state["prompt"] = random.choice(PROMPTS)
        _state["last_day"] = today
        _state["spins"] += 1
    return jsonify({"date": today, "prompt": _state["prompt"], "by": who})


@roulette_bp.route("/api/muse/roulette/done", methods=["POST"])
def mr_done():
    _state["streak"] += 1
    return jsonify(
        {
            "streak": _state["streak"],
            "msg": f"Racha creativa: {_state['streak']} días. La musa te saluda.",
        }
    )


@roulette_bp.route("/api/muse/roulette/web")
def mr_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Muse Roulette</title>
<style>body{background:#12041f;color:#ff9de2;font-family:monospace;text-align:center;padding:60px}
#pr{font-size:24px;margin:30px;min-height:60px}
button{background:#ff2e88;color:#fff;border:0;padding:14px 34px;border-radius:30px;font-size:18px;cursor:pointer}</style>
</head><body><h2>🎰 MUSE ROULETTE</h2><div id="pr">...</div>
<button onclick="spin()">Girar</button>
<script>function spin(){fetch('/api/muse/roulette/spin',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(r=>r.json()).then(d=>{document.getElementById('pr').textContent=d.prompt})}</script>
</body></html>"""

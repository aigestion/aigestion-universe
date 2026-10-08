import random

from flask import Blueprint, jsonify, request

radio_bp = Blueprint("astral_radio", __name__)
_state = {"tuned": 0, "station": "nebula"}

PHRASES = [
    "Respira... las estrellas giran despacio sobre ti...",
    "Tu cuerpo es una nube que flota sobre un mar tibio...",
    "Cada número que cuento te hunde un poco más en la calma...",
    "La luna tararea una canción que solo tú escuchas...",
    "Suelta los hombros... suelta el día... suelta todo...",
    "Un tren suave cruza la noche llevándote al país de los sueños...",
]
TRACKS = ["lluvia + pads", "olas + piano", "bosque nocturno", "drones 432Hz", "chimenea + viento"]


@radio_bp.route("/api/dreams/radio/tune", methods=["POST"])
def ar_tune():
    data = request.json or {}
    _state["station"] = data.get("station", "nebula")
    _state["tuned"] += 1
    return jsonify(
        {
            "station": _state["station"],
            "phrase": random.choice(PHRASES),
            "track": random.choice(TRACKS),
        }
    )


@radio_bp.route("/api/dreams/radio/next")
def ar_next():
    return jsonify(
        {
            "phrase": random.choice(PHRASES),
            "track": random.choice(TRACKS),
            "station": _state["station"],
        }
    )


@radio_bp.route("/api/dreams/radio/web")
def ar_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Astral Radio</title>
<style>body{margin:0;background:radial-gradient(circle at 50% 30%,#1a0033,#050510);color:#c9a7ff;font-family:monospace;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;text-align:center}
.stars{font-size:48px;animation:tw 2s infinite}@keyframes tw{50%{opacity:.4}}
#ph{max-width:600px;font-size:20px;margin:20px;min-height:60px}
button{background:#7b2fff;color:#fff;border:0;padding:12px 28px;border-radius:24px;font-size:16px;cursor:pointer}
</style></head><body>
<div class="stars">✦ ⋆ ✧ ⋆ ✦</div><h2>ASTRAL RADIO</h2>
<p id="ph">Sintonizando el dial onírico...</p><p id="tr"></p>
<button onclick="next()">Siguiente susurro</button>
<script>function next(){fetch('/api/dreams/radio/next').then(r=>r.json()).then(d=>{document.getElementById('ph').textContent=d.phrase;document.getElementById('tr').textContent='♪ '+d.track})}next();setInterval(next,20000)</script>
</body></html>"""

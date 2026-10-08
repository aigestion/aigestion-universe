import random

from flask import Blueprint, jsonify, request

cow_bp = Blueprint("story_cowriter", __name__)
_state = {"stories": [], "next_id": 1}

TWISTS = [
    "...pero la puerta que creía cerrada estaba abierta desde dentro.",
    "...entonces descubrió que la carta la había escrito él mismo.",
    "...y el desconocido sonrió: 'por fin despertaste'.",
    "...el reloj marcó las 13:00 y todo se detuvo un segundo.",
]
BRIDGES = [
    "El viento trajo un olor a {x} y todo cambió.",
    "Dudó un instante, y en ese instante decidió {y}.",
    "Lo que nadie sabía era que {x} guardaba un secreto.",
]


@cow_bp.route("/api/muse/cowrite/start", methods=["POST"])
def cw_start():
    data = request.json or {}
    s = {
        "id": _state["next_id"],
        "prompt": data.get("prompt", "Érase una vez..."),
        "parts": [data.get("prompt", "Érase una vez...")],
    }
    _state["stories"].append(s)
    _state["next_id"] += 1
    return jsonify(s)


@cow_bp.route("/api/muse/cowrite/continue", methods=["POST"])
def cw_continue():
    data = request.json or {}
    s = next((x for x in _state["stories"] if x["id"] == data.get("id")), None)
    if not s:
        return jsonify({"error": "not found"}), 404
    nxt = random.choice(BRIDGES).format(x=data.get("palabra", "la noche"), y="seguir adelante")
    if data.get("twist"):
        nxt += " " + random.choice(TWISTS)
    s["parts"].append(nxt)
    return jsonify({"id": s["id"], "continuation": nxt, "full": " ".join(s["parts"])})

from flask import Blueprint, jsonify, request

anchor_bp = Blueprint("calm_anchor", __name__)
_state = {"uses": 0}

STEPS_478 = [
    "Inhala por la nariz 4 segundos",
    "Sostén 7 segundos",
    "Exhala por la boca 8 segundos",
    "Repite 3 ciclos",
]
GROUND = ["5 cosas que ves", "4 que tocas", "3 que oyes", "2 que hueles", "1 que saboreas"]
MANTRAS = [
    "Esto pasará. Ya pasó antes.",
    "Estoy a salvo en este momento.",
    "Respiro y el cuerpo obedece.",
    "Una ola: sube, rompe, se va.",
]


@anchor_bp.route("/api/guardian/calm/start", methods=["POST"])
def ca_start():
    _state["uses"] += 1
    data = request.json or {}
    level = int(data.get("level", 5))
    return jsonify(
        {
            "level": level,
            "msg": f"Nivel {level}/10. Vamos a bajarlo juntos, paso a paso.",
            "uses": _state["uses"],
        }
    )


@anchor_bp.route("/api/guardian/calm/breathe")
def ca_breathe():
    return jsonify({"technique": "4-7-8", "steps": STEPS_478})


@anchor_bp.route("/api/guardian/calm/ground")
def ca_ground():
    import random

    return jsonify({"grounding": GROUND, "mantra": random.choice(MANTRAS)})

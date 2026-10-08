import random

from flask import Blueprint, jsonify, request

twist_bp = Blueprint("plot_twister", __name__)
_state = {"twists_served": 0}

TWISTS = {
    "misterio": [
        "El detective era el culpable.",
        "La víctima fingió su muerte.",
        "Todo ocurrió un año antes.",
    ],
    "romance": [
        "La carta nunca se envió... hasta hoy.",
        "Eran la misma persona en dos tiempos.",
        "El rival era su mejor aliado.",
    ],
    "scifi": [
        "La IA protegía a los humanos de sí mismos.",
        "El planeta era una simulación de examen.",
        "Volver atrás borraba al que vuelve.",
    ],
    "fantasia": [
        "La profecía hablaba del villano, no del héroe.",
        "La magia cobraba recuerdos como precio.",
        "El dragón era el último rey.",
    ],
}


@twist_bp.route("/api/muse/twist/spin")
def pt_spin():
    genre = request.args.get("genre", "misterio")
    pool = TWISTS.get(genre, TWISTS["misterio"])
    _state["twists_served"] += 1
    return jsonify({"genre": genre, "twist": random.choice(pool)})


@twist_bp.route("/api/muse/twist/foreshadow", methods=["POST"])
def pt_fore():
    data = request.json or {}
    twist = data.get("twist", "")
    clues = [
        "Un objeto que aparece 3 veces: {}.".format(data.get("objeto", "una llave")),
        "Un personaje que miente en algo pequeño (pista del gran engaño).",
        "Una frase que se repite y cambia de sentido al final.",
    ]
    return jsonify(
        {
            "twist": twist,
            "planted_clues": clues,
            "check": "Si quitas el giro, ¿las pistas siguen teniendo sentido inocente? Deben.",
        }
    )

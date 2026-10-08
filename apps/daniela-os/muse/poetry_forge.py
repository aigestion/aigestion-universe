import random

from flask import Blueprint, jsonify, request

poetry_bp = Blueprint("poetry_forge", __name__)
_state = {"poems": 0}

WORDS = {
    "luna": ["cuna", "laguna", "fortuna"],
    "mar": ["soñar", "cantar", "hogar"],
    "noche": ["derroche", "reproche", "coche"],
    "viento": ["siento", "cuento", "momento"],
    "amor": ["temblor", "esplendor", "verdadero amor"],
}
SEEDS = [
    "la luna sobre el mar",
    "un tren que no vuelve",
    "lluvia en la ventana",
    "el café de las seis",
    "cartas sin enviar",
]


@poetry_bp.route("/api/muse/poetry/forge", methods=["POST"])
def pf_forge():
    data = request.json or {}
    forma = data.get("forma", "libre")
    tema = data.get("tema", random.choice(SEEDS))
    _state["poems"] += 1
    if forma == "haiku":
        poem = (
            f"{tema.capitalize()} despierta\nsilencio entre dos luces\n{tema.split()[-1]} respira"
        )
    elif forma == "soneto":
        poem = f"Soneto a {tema}:\n" + "\n".join(f"verso {i} de sombra y luz" for i in range(1, 5))
    else:
        poem = f"{tema.capitalize()}:\nversos que caen como lluvia lenta,\n{tema} en la boca,\nsilencio que canta."
    return jsonify({"forma": forma, "tema": tema, "poem": poem})


@poetry_bp.route("/api/muse/poetry/rhyme")
def pf_rhyme():
    w = request.args.get("w", "luna").lower()
    return jsonify(
        {"word": w, "rhymes": WORDS.get(w, ["prueba con: luna, mar, noche, viento, amor"])}
    )


@poetry_bp.route("/api/muse/poetry/stats")
def pf_stats():
    return jsonify(_state)

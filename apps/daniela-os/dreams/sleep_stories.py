import random
import time

from flask import Blueprint, jsonify, request

stories_bp = Blueprint("sleep_stories", __name__)
_state = {"stories": [], "next_id": 1}

OPENERS = {
    "bosque": "En un bosque donde los árboles susurran al viento...",
    "mar": "Las olas mecían suavemente la orilla bajo la luna...",
    "montaña": "En lo alto de una montaña dormida entre nubes...",
    "espacio": "Entre estrellas que parpadeaban como luciérnagas...",
    "general": "Había una vez un lugar donde el tiempo caminaba despacio...",
}
CLOSERS = [
    "y poco a poco todo se quedó en calma... buenas noches.",
    "y el sueño llegó como una manta tibia... descansa.",
    "y las estrellas velaron su sueño hasta el amanecer.",
]


@stories_bp.route("/api/dreams/stories/generate", methods=["POST"])
def st_generate():
    data = request.json or {}
    tema = data.get("tema", "general")
    duracion = int(data.get("duracion", 5))
    opener = OPENERS.get(tema, OPENERS["general"])
    body = " ".join(
        random.choice(
            [
                "El aire olía a calma y a hogar.",
                "Cada respiración era más lenta que la anterior.",
                "Los sonidos se volvían suaves, lejanos, dulces.",
                "Nada urgía, nada pesaba, todo flotaba.",
            ]
        )
        for _ in range(max(duracion, 1))
    )
    text = f"{opener} {body} {random.choice(CLOSERS)}"
    story = {
        "id": _state["next_id"],
        "tema": tema,
        "duracion": duracion,
        "text": text,
        "ts": time.time(),
    }
    _state["stories"].append(story)
    _state["next_id"] += 1
    return jsonify(story)


@stories_bp.route("/api/dreams/stories/library")
def st_library():
    return jsonify(_state["stories"])


@stories_bp.route("/api/dreams/stories/get/<int:sid>")
def st_get(sid):
    for s in _state["stories"]:
        if s["id"] == sid:
            return jsonify(s)
    return jsonify({"error": "not found"}), 404

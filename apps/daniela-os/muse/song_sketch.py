from flask import Blueprint, jsonify, request

song_bp = Blueprint("song_sketch", __name__)
_state = {"songs": [], "next_id": 1}
STRUCTS = {
    "pop": ["verso", "pre", "estribillo", "verso", "estribillo", "puente", "estribillo"],
    "balada": ["verso", "verso", "estribillo", "verso", "estribillo"],
    "rap": ["intro", "verso16", "hook", "verso16", "hook", "outro"],
}


def _syllables(line):
    vowels = "aeiouáéíóúü"
    n, prev = 0, False
    for ch in line.lower():
        is_v = ch in vowels
        if is_v and not prev:
            n += 1
        prev = is_v
    return max(n, 1)


@song_bp.route("/api/muse/song/sketch", methods=["POST"])
def sk_sketch():
    data = request.json or {}
    genre = data.get("genero", "pop")
    s = {
        "id": _state["next_id"],
        "title": data.get("title", "Sin título"),
        "genero": genre,
        "structure": STRUCTS.get(genre, STRUCTS["pop"]),
        "lines": data.get("lines", []),
    }
    _state["songs"].append(s)
    _state["next_id"] += 1
    return jsonify(s)


@song_bp.route("/api/muse/song/meter", methods=["POST"])
def sk_meter():
    data = request.json or {}
    counts = [_syllables(line) for line in data.get("lines", [])]
    even = len(set(counts)) <= 2 if counts else True
    return jsonify(
        {
            "syllables": counts,
            "verdict": "Métrica pareja, canta bien."
            if even
            else "Métrica irregular: ajusta sílabas por verso.",
        }
    )

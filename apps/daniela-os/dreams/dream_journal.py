import time

from flask import Blueprint, jsonify, request

journal_bp = Blueprint("dream_journal", __name__)
_state = {"dreams": [], "next_id": 1}

KEYWORDS = {
    "volar": "libertad, deseo de soltar control",
    "agua": "emociones, estado del inconsciente",
    "persegu": "evitación, algo pendiente que te alcanza",
    "diente": "inseguridad, miedo a perder imagen",
    "casa": "el yo, habitaciones = áreas de tu vida",
    "muerte": "fin de etapa, transformación",
}


@journal_bp.route("/api/dreams/journal/add", methods=["POST"])
def dj_add():
    data = request.json or {}
    entry = {
        "id": _state["next_id"],
        "title": data.get("title", "Sin título"),
        "text": data.get("text", ""),
        "mood": data.get("mood", "neutral"),
        "lucid": bool(data.get("lucid", False)),
        "ts": time.time(),
    }
    _state["dreams"].append(entry)
    _state["next_id"] += 1
    return jsonify(entry)


@journal_bp.route("/api/dreams/journal/list")
def dj_list():
    return jsonify(_state["dreams"])


@journal_bp.route("/api/dreams/journal/search")
def dj_search():
    q = request.args.get("q", "").lower()
    hits = [d for d in _state["dreams"] if q in d["title"].lower() or q in d["text"].lower()]
    return jsonify(hits)


@journal_bp.route("/api/dreams/journal/interpret/<int:did>")
def dj_interpret(did):
    entry = next((d for d in _state["dreams"] if d["id"] == did), None)
    if not entry:
        return jsonify({"error": "not found"}), 404
    text = (entry["title"] + " " + entry["text"]).lower()
    found = [{"symbol": k, "meaning": v} for k, v in KEYWORDS.items() if k in text]
    note = "Sueño lúcido: gran consciencia onírica." if entry["lucid"] else "Sueño normal."
    return jsonify({"id": did, "symbols": found, "note": note})

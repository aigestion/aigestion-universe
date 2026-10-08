import time

from flask import Blueprint, jsonify, request

will_bp = Blueprint("digital_will", __name__)
_state = {"entries": [], "legacy_contacts": [], "next_id": 1}


@will_bp.route("/api/guardian/will/add", methods=["POST"])
def dw_add():
    data = request.json or {}
    e = {
        "id": _state["next_id"],
        "cuenta": data.get("cuenta", ""),
        "instruccion": data.get("instruccion", ""),
        "ts": time.time(),
    }
    _state["entries"].append(e)
    _state["next_id"] += 1
    return jsonify(e)


@will_bp.route("/api/guardian/will/legacy_contact", methods=["POST"])
def dw_legacy():
    data = request.json or {}
    c = {
        "name": data.get("name", ""),
        "relation": data.get("relation", ""),
        "scope": data.get("scope", "todo"),
    }
    _state["legacy_contacts"].append(c)
    return jsonify(c)


@will_bp.route("/api/guardian/will/summary")
def dw_summary():
    return jsonify(
        {
            "accounts": len(_state["entries"]),
            "legacy_contacts": _state["legacy_contacts"],
            "tip": "Guarda copia impresa en sobre sellado con alguien de confianza.",
        }
    )

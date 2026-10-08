import time

from flask import Blueprint, jsonify, request

garden_bp = Blueprint("idea_garden", __name__)
_state = {"seeds": [], "next_id": 1}
STAGES = ["semilla", "brote", "flor", "fruto"]
HINTS = {
    "semilla": "Riega: escribe 3 líneas sobre ella.",
    "brote": "Dale sol: cuéntasela a alguien.",
    "flor": "Poliniza: combina con otra idea.",
    "fruto": "Cosecha: define el primer paso real.",
}


@garden_bp.route("/api/muse/garden/plant", methods=["POST"])
def ig_plant():
    data = request.json or {}
    s = {
        "id": _state["next_id"],
        "title": data.get("title", "Idea"),
        "stage": "semilla",
        "ts": time.time(),
    }
    _state["seeds"].append(s)
    _state["next_id"] += 1
    return jsonify(s)


@garden_bp.route("/api/muse/garden/grow/<int:sid>", methods=["POST"])
def ig_grow(sid):
    s = next((x for x in _state["seeds"] if x["id"] == sid), None)
    if not s:
        return jsonify({"error": "not found"}), 404
    i = STAGES.index(s["stage"])
    if i < len(STAGES) - 1:
        s["stage"] = STAGES[i + 1]
    return jsonify({"id": sid, "stage": s["stage"], "next_hint": HINTS[s["stage"]]})


@garden_bp.route("/api/muse/garden/list")
def ig_list():
    return jsonify([{**s, "hint": HINTS[s["stage"]]} for s in _state["seeds"]])

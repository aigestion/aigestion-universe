import time

from flask import Blueprint, jsonify, request

storm_bp = Blueprint("brainstorm_storm", __name__)
_state = {"sessions": [], "next_id": 1}


@storm_bp.route("/api/muse/storm/start", methods=["POST"])
def bs_start():
    data = request.json or {}
    s = {
        "id": _state["next_id"],
        "topic": data.get("topic", "ideas"),
        "modo_loco": bool(data.get("modo_loco", False)),
        "ideas": [],
        "timer_min": int(data.get("timer_min", 10)),
        "ts": time.time(),
    }
    _state["sessions"].append(s)
    _state["next_id"] += 1
    sparks = (
        [
            "¿Y si fuera 10x más grande?",
            "¿Y si fuera gratis?",
            "¿Y si lo hiciera un niño?",
            "¿Y si fuera ilegal no hacerlo?",
        ]
        if s["modo_loco"]
        else []
    )
    return jsonify({**s, "sparks": sparks})


@storm_bp.route("/api/muse/storm/add", methods=["POST"])
def bs_add():
    data = request.json or {}
    s = next((x for x in _state["sessions"] if x["id"] == data.get("id")), None)
    if not s:
        return jsonify({"error": "not found"}), 404
    idea = {"text": data.get("idea", ""), "votes": 0}
    s["ideas"].append(idea)
    return jsonify(idea)


@storm_bp.route("/api/muse/storm/vote", methods=["POST"])
def bs_vote():
    data = request.json or {}
    s = next((x for x in _state["sessions"] if x["id"] == data.get("id")), None)
    if not s:
        return jsonify({"error": "not found"}), 404
    for i in s["ideas"]:
        if i["text"] == data.get("idea"):
            i["votes"] += 1
    ranked = sorted(s["ideas"], key=lambda x: x["votes"], reverse=True)
    return jsonify({"ranking": ranked})

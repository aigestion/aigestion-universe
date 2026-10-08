from flask import Blueprint, jsonify, request

reunion_bp = Blueprint("reunion_optimizer", __name__)
_state = {"options": [], "votes": {}}


@reunion_bp.route("/api/social/reunion/propose", methods=["POST"])
def ro_propose():
    data = request.json or {}
    for d in data.get("fechas", []):
        if d not in _state["options"]:
            _state["options"].append(d)
            _state["votes"][d] = []
    return jsonify({"options": _state["options"]})


@reunion_bp.route("/api/social/reunion/vote", methods=["POST"])
def ro_vote():
    data = request.json or {}
    fecha, who = data.get("fecha", ""), data.get("who", "?")
    if fecha in _state["votes"] and who not in _state["votes"][fecha]:
        _state["votes"][fecha].append(who)
    return jsonify({"votes": _state["votes"]})


@reunion_bp.route("/api/social/reunion/best")
def ro_best():
    if not _state["votes"]:
        return jsonify({"best": None})
    best = max(_state["votes"], key=lambda d: len(_state["votes"][d]))
    return jsonify({"best": best, "votes": len(_state["votes"][best]), "all": _state["votes"]})

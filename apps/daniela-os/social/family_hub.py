import time

from flask import Blueprint, jsonify, request

family_bp = Blueprint("family_hub", __name__)
_state = {"members": [], "events": [], "next_id": 1}


@family_bp.route("/api/social/family/add", methods=["POST"])
def fh_add():
    data = request.json or {}
    m = {
        "id": _state["next_id"],
        "name": data.get("name", "?"),
        "role": data.get("role", "miembro"),
        "ts": time.time(),
    }
    _state["members"].append(m)
    _state["next_id"] += 1
    return jsonify(m)


@family_bp.route("/api/social/family/members")
def fh_members():
    return jsonify(_state["members"])


@family_bp.route("/api/social/family/event", methods=["POST"])
def fh_event():
    data = request.json or {}
    e = {
        "name": data.get("name", "Encuentro"),
        "date": data.get("date", ""),
        "who": data.get("who", []),
        "ts": time.time(),
    }
    _state["events"].append(e)
    return jsonify(e)


@family_bp.route("/api/social/family/events")
def fh_events():
    return jsonify(_state["events"])

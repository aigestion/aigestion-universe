import time

from flask import Blueprint, jsonify, request

map_bp = Blueprint("milestone_map", __name__)
_state = {"milestones": [], "next_id": 1}


@map_bp.route("/api/temporal/milestones/add", methods=["POST"])
def mm_add():
    data = request.json or {}
    m = {
        "id": _state["next_id"],
        "title": data.get("title", "Hito"),
        "date": data.get("date", "2000-01-01"),
        "kind": data.get("kind", "personal"),
        "note": data.get("note", ""),
        "ts": time.time(),
    }
    _state["milestones"].append(m)
    _state["next_id"] += 1
    return jsonify(m)


@map_bp.route("/api/temporal/milestones/timeline")
def mm_timeline():
    return jsonify(sorted(_state["milestones"], key=lambda x: x["date"]))


@map_bp.route("/api/temporal/milestones/delete/<int:mid>", methods=["POST"])
def mm_del(mid):
    _state["milestones"] = [m for m in _state["milestones"] if m["id"] != mid]
    return jsonify({"ok": True})

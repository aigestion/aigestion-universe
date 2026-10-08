import time
from datetime import datetime

from flask import Blueprint, jsonify, request

cap_bp = Blueprint("time_capsule", __name__)
_state = {"capsules": [], "next_id": 1}


@cap_bp.route("/api/temporal/capsule/seal", methods=["POST"])
def tc_seal():
    data = request.json or {}
    cap = {
        "id": _state["next_id"],
        "message": data.get("message", ""),
        "open_at": data.get("open_at", ""),
        "sealed": True,
        "ts": time.time(),
    }
    _state["capsules"].append(cap)
    _state["next_id"] += 1
    return jsonify({"id": cap["id"], "sealed": True})


@cap_bp.route("/api/temporal/capsule/list")
def tc_list():
    now = datetime.now()
    out = []
    for c in _state["capsules"]:
        try:
            openable = now >= datetime.strptime(c["open_at"], "%Y-%m-%d")
        except ValueError:
            openable = False
        out.append(
            {"id": c["id"], "open_at": c["open_at"], "status": "unsealed" if openable else "sealed"}
        )
    return jsonify(out)


@cap_bp.route("/api/temporal/capsule/open/<int:cid>")
def tc_open(cid):
    cap = next((c for c in _state["capsules"] if c["id"] == cid), None)
    if not cap:
        return jsonify({"error": "not found"}), 404
    try:
        openable = datetime.now() >= datetime.strptime(cap["open_at"], "%Y-%m-%d")
    except ValueError:
        openable = False
    if not openable:
        return jsonify(
            {
                "sealed": True,
                "open_at": cap["open_at"],
                "msg": "Aún sellada. La paciencia es parte del ritual.",
            }
        )
    cap["sealed"] = False
    return jsonify({"sealed": False, "message": cap["message"]})

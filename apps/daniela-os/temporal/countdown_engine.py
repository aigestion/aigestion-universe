import time
from datetime import datetime

from flask import Blueprint, jsonify, request

cd_bp = Blueprint("countdown_engine", __name__)
_state = {"events": [], "next_id": 1}
MILESTONES = [50, 25, 10, 1]


@cd_bp.route("/api/temporal/countdown/add", methods=["POST"])
def cd_add():
    data = request.json or {}
    ev = {
        "id": _state["next_id"],
        "name": data.get("name", "Evento"),
        "target": data.get("target", ""),
        "ts": time.time(),
    }
    _state["events"].append(ev)
    _state["next_id"] += 1
    return jsonify(ev)


@cd_bp.route("/api/temporal/countdown/list")
def cd_list():
    now = datetime.now()
    out = []
    for e in _state["events"]:
        try:
            t = datetime.strptime(e["target"], "%Y-%m-%d")
            days = (t - now).days
        except ValueError:
            days = None
        passed = [m for m in MILESTONES if days is not None and days <= m]
        out.append({**e, "days_left": days, "milestones_hit": passed})
    return jsonify(out)


@cd_bp.route("/api/temporal/countdown/delete/<int:eid>", methods=["POST"])
def cd_del(eid):
    _state["events"] = [e for e in _state["events"] if e["id"] != eid]
    return jsonify({"ok": True})

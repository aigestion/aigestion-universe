import time
from datetime import datetime

from flask import Blueprint, jsonify, request

meds_bp = Blueprint("med_reminder", __name__)
_state = {"meds": [], "taken": [], "next_id": 1}


@meds_bp.route("/api/guardian/meds/add", methods=["POST"])
def mr_add():
    data = request.json or {}
    m = {
        "id": _state["next_id"],
        "name": data.get("name", "?"),
        "dosis": data.get("dosis", ""),
        "horario": data.get("horario", []),
        "ts": time.time(),
    }
    _state["meds"].append(m)
    _state["next_id"] += 1
    return jsonify(m)


@meds_bp.route("/api/guardian/meds/taken", methods=["POST"])
def mr_taken():
    data = request.json or {}
    rec = {
        "med_id": data.get("med_id"),
        "ts": time.time(),
        "day": datetime.now().strftime("%Y-%m-%d"),
    }
    _state["taken"].append(rec)
    return jsonify({"ok": True})


@meds_bp.route("/api/guardian/meds/adherence")
def mr_adh():
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    for m in _state["meds"]:
        doses = len(m["horario"]) or 1
        got = sum(1 for t in _state["taken"] if t["med_id"] == m["id"] and t["day"] == today)
        out.append(
            {
                "name": m["name"],
                "adherence_pct": round(min(got / doses, 1.0) * 100, 1),
                "taken": got,
                "expected": doses,
            }
        )
    return jsonify(out)


@meds_bp.route("/api/guardian/meds/list")
def mr_list():
    return jsonify(_state["meds"])

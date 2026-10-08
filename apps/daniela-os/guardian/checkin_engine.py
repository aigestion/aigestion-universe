import time

from flask import Blueprint, jsonify, request

checkin_bp = Blueprint("checkin_engine", __name__)
_state = {"schedules": [], "log": [], "next_id": 1}


@checkin_bp.route("/api/guardian/checkin/schedule", methods=["POST"])
def ce_sched():
    data = request.json or {}
    s = {
        "id": _state["next_id"],
        "who": data.get("who", "yo"),
        "every_min": int(data.get("every_min", 120)),
        "last_ok": time.time(),
        "status": "ok",
    }
    _state["schedules"].append(s)
    _state["next_id"] += 1
    return jsonify(s)


@checkin_bp.route("/api/guardian/checkin/ok/<int:sid>", methods=["POST"])
def ce_ok(sid):
    s = next((x for x in _state["schedules"] if x["id"] == sid), None)
    if not s:
        return jsonify({"error": "not found"}), 404
    s["last_ok"] = time.time()
    s["status"] = "ok"
    _state["log"].append({"sid": sid, "ev": "ok", "ts": time.time()})
    return jsonify({"ok": True})


@checkin_bp.route("/api/guardian/checkin/status")
def ce_status():
    now = time.time()
    out = []
    for s in _state["schedules"]:
        late = (now - s["last_ok"]) > s["every_min"] * 60
        missed = (now - s["last_ok"]) > s["every_min"] * 120
        s["status"] = "missed" if missed else ("late" if late else "ok")
        out.append(
            {
                **s,
                "escalation": "ESCALAR: avisar contactos"
                if missed
                else ("atento" if late else "none"),
            }
        )
    return jsonify(out)

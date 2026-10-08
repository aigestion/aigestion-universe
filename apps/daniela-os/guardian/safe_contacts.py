import time

from flask import Blueprint, jsonify, request

safe_bp = Blueprint("safe_contacts", __name__)
_state = {"contacts": [], "next_id": 1}


@safe_bp.route("/api/guardian/contacts/add", methods=["POST"])
def sc_add():
    data = request.json or {}
    c = {
        "id": _state["next_id"],
        "name": data.get("name", "?"),
        "phone": data.get("phone", ""),
        "prioridad": int(data.get("prioridad", 3)),
        "verified": False,
        "ts": time.time(),
    }
    _state["contacts"].append(c)
    _state["next_id"] += 1
    return jsonify(c)


@safe_bp.route("/api/guardian/contacts/verify/<int:cid>", methods=["POST"])
def sc_verify(cid):
    c = next((x for x in _state["contacts"] if x["id"] == cid), None)
    if not c:
        return jsonify({"error": "not found"}), 404
    c["verified"] = True
    return jsonify({"ok": True})


@safe_bp.route("/api/guardian/contacts/list")
def sc_list():
    return jsonify(sorted(_state["contacts"], key=lambda x: x["prioridad"]))

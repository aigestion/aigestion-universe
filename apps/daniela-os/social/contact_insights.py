import time

from flask import Blueprint, jsonify, request

contacts_bp = Blueprint("contact_insights", __name__)
_state = {"contacts": [], "next_id": 1}


@contacts_bp.route("/api/social/contacts/add", methods=["POST"])
def ci_add():
    data = request.json or {}
    c = {
        "id": _state["next_id"],
        "name": data.get("name", "?"),
        "relation": data.get("relation", "amigo"),
        "last_talk": time.time(),
        "ts": time.time(),
    }
    _state["contacts"].append(c)
    _state["next_id"] += 1
    return jsonify(c)


@contacts_bp.route("/api/social/contacts/list")
def ci_list():
    now = time.time()
    out = [{**c, "days_silent": int((now - c["last_talk"]) // 86400)} for c in _state["contacts"]]
    return jsonify(sorted(out, key=lambda x: x["days_silent"], reverse=True))


@contacts_bp.route("/api/social/contacts/ping/<int:cid>", methods=["POST"])
def ci_ping(cid):
    c = next((x for x in _state["contacts"] if x["id"] == cid), None)
    if not c:
        return jsonify({"error": "not found"}), 404
    c["last_talk"] = time.time()
    return jsonify(
        {"ok": True, "nudge": "“Hola {}, me acordé de ti. ¿Cómo va todo?”".format(c["name"])}
    )


@contacts_bp.route("/api/social/contacts/nudges")
def ci_nudges():
    now = time.time()
    quiet = [c["name"] for c in _state["contacts"] if (now - c["last_talk"]) > 14 * 86400]
    return jsonify({"need_nudge": quiet})

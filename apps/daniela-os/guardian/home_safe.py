import time

from flask import Blueprint, jsonify, request

home_bp = Blueprint("home_safe", __name__)
_state = {"trips": [], "next_id": 1}


@home_bp.route("/api/guardian/homesafe/start", methods=["POST"])
def hs_start():
    data = request.json or {}
    eta_min = int(data.get("eta_min", 30))
    t = {
        "id": _state["next_id"],
        "origen": data.get("origen", ""),
        "destino": data.get("destino", ""),
        "expires_at": time.time() + eta_min * 60,
        "arrived": False,
        "alerted": False,
    }
    _state["trips"].append(t)
    _state["next_id"] += 1
    return jsonify({"id": t["id"], "eta_min": eta_min})


@home_bp.route("/api/guardian/homesafe/arrived/<int:tid>", methods=["POST"])
def hs_arrived(tid):
    t = next((x for x in _state["trips"] if x["id"] == tid), None)
    if not t:
        return jsonify({"error": "not found"}), 404
    t["arrived"] = True
    return jsonify({"ok": True, "msg": "¡Bien en casa! 🏠"})


@home_bp.route("/api/guardian/homesafe/status/<int:tid>")
def hs_status(tid):
    t = next((x for x in _state["trips"] if x["id"] == tid), None)
    if not t:
        return jsonify({"error": "not found"}), 404
    if not t["arrived"] and time.time() > t["expires_at"]:
        t["alerted"] = True
    return jsonify({**t, "remaining_s": max(0, int(t["expires_at"] - time.time()))})

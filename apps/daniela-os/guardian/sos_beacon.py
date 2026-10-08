import time

from flask import Blueprint, jsonify, request

sos_bp = Blueprint("sos_beacon", __name__)
_state = {"active": None, "history": []}


@sos_bp.route("/api/guardian/sos/activate", methods=["POST"])
def sos_on():
    data = request.json or {}
    _state["active"] = {
        "contacts": data.get("contacts", []),
        "message": data.get("message", "¡NECESITO AYUDA!"),
        "location": data.get("location", ""),
        "cancel_in_s": int(data.get("cancel_in_s", 30)),
        "ts": time.time(),
    }
    _state["history"].append({**_state["active"], "ev": "activated"})
    return jsonify(
        {
            "sos": "ACTIVE",
            "cancel_window_s": _state["active"]["cancel_in_s"],
            "will_notify": _state["active"]["contacts"],
        }
    )


@sos_bp.route("/api/guardian/sos/cancel", methods=["POST"])
def sos_off():
    if _state["active"]:
        _state["history"].append({"ev": "cancelled", "ts": time.time()})
        _state["active"] = None
    return jsonify({"sos": "cancelled"})


@sos_bp.route("/api/guardian/sos/status")
def sos_status():
    if not _state["active"]:
        return jsonify({"sos": "idle"})
    elapsed = time.time() - _state["active"]["ts"]
    left = _state["active"]["cancel_in_s"] - elapsed
    return jsonify(
        {
            "sos": "ACTIVE",
            "cancel_left_s": max(0, int(left)),
            "escalated": left <= 0,
            "info": _state["active"],
        }
    )

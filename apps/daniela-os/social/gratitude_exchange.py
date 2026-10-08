import time
from datetime import datetime

from flask import Blueprint, jsonify, request

grat_bp = Blueprint("gratitude_exchange", __name__)
_state = {"entries": [], "streak": 0, "last_day": ""}


@grat_bp.route("/api/social/gratitude/give", methods=["POST"])
def ge_give():
    data = request.json or {}
    today = datetime.now().strftime("%Y-%m-%d")
    if _state["last_day"] != today:
        _state["streak"] = _state["streak"] + 1 if _state["last_day"] else 1
        _state["last_day"] = today
    e = {
        "to": data.get("to", ""),
        "text": data.get("text", ""),
        "direction": "dada",
        "ts": time.time(),
    }
    _state["entries"].append(e)
    return jsonify({**e, "streak": _state["streak"]})


@grat_bp.route("/api/social/gratitude/receive", methods=["POST"])
def ge_receive():
    data = request.json or {}
    e = {
        "to": "yo",
        "from": data.get("from", ""),
        "text": data.get("text", ""),
        "direction": "recibida",
        "ts": time.time(),
    }
    _state["entries"].append(e)
    return jsonify(e)


@grat_bp.route("/api/social/gratitude/list")
def ge_list():
    return jsonify({"entries": _state["entries"], "streak": _state["streak"]})

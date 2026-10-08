import time
from datetime import datetime

from flask import Blueprint, jsonify, request

letters_bp = Blueprint("future_letters", __name__)
_state = {"letters": [], "next_id": 1}


@letters_bp.route("/api/temporal/letters/write", methods=["POST"])
def fl_write():
    data = request.json or {}
    letter = {
        "id": _state["next_id"],
        "to": data.get("to", "yo futuro"),
        "body": data.get("body", ""),
        "deliver_at": data.get("deliver_at", ""),
        "delivered": False,
        "ts": time.time(),
    }
    _state["letters"].append(letter)
    _state["next_id"] += 1
    return jsonify(letter)


@letters_bp.route("/api/temporal/letters/pending")
def fl_pending():
    now = datetime.now()
    out = []
    for letter in _state["letters"]:
        try:
            due = now >= datetime.strptime(letter["deliver_at"], "%Y-%m-%d")
        except ValueError:
            due = False
        if due and not letter["delivered"]:
            letter["delivered"] = True
        out.append(
            {
                "id": letter["id"],
                "to": letter["to"],
                "deliver_at": letter["deliver_at"],
                "delivered": letter["delivered"],
                "body": letter["body"] if letter["delivered"] else None,
            }
        )
    return jsonify(out)


@letters_bp.route("/api/temporal/letters/list")
def fl_list():
    return jsonify(
        [
            {
                "id": letter["id"],
                "to": letter["to"],
                "deliver_at": letter["deliver_at"],
                "delivered": letter["delivered"],
            }
            for letter in _state["letters"]
        ]
    )

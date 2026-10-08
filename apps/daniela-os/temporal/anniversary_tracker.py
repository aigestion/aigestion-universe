import time
from datetime import datetime

from flask import Blueprint, jsonify, request

anni_bp = Blueprint("anniversary_tracker", __name__)
_state = {"items": [], "next_id": 1}


def _days_left(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
    now = datetime.now()
    nxt = d.replace(year=now.year)
    if nxt < now:
        nxt = nxt.replace(year=now.year + 1)
    return (nxt - now).days


@anni_bp.route("/api/temporal/anniversary/add", methods=["POST"])
def an_add():
    data = request.json or {}
    item = {
        "id": _state["next_id"],
        "name": data.get("name", "Aniversario"),
        "date": data.get("date", "2000-01-01"),
        "reminder_days": int(data.get("reminder_days", 7)),
        "ts": time.time(),
    }
    _state["items"].append(item)
    _state["next_id"] += 1
    return jsonify(item)


@anni_bp.route("/api/temporal/anniversary/list")
def an_list():
    out = []
    for i in _state["items"]:
        days = _days_left(i["date"])
        out.append(
            {**i, "days_left": days, "remind": days is not None and days <= i["reminder_days"]}
        )
    return jsonify(sorted(out, key=lambda x: x["days_left"] if x["days_left"] is not None else 999))


@anni_bp.route("/api/temporal/anniversary/delete/<int:aid>", methods=["POST"])
def an_del(aid):
    _state["items"] = [i for i in _state["items"] if i["id"] != aid]
    return jsonify({"ok": True})

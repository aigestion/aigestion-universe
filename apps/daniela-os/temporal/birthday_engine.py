import time
from datetime import datetime

from flask import Blueprint, jsonify, request

bday_bp = Blueprint("birthday_engine", __name__)
_state = {"people": [], "next_id": 1}

ZODIAC = [
    (1, 19, "Capricornio"),
    (2, 18, "Acuario"),
    (3, 20, "Piscis"),
    (4, 19, "Aries"),
    (5, 20, "Tauro"),
    (6, 20, "Géminis"),
    (7, 22, "Cáncer"),
    (8, 22, "Leo"),
    (9, 22, "Virgo"),
    (10, 22, "Libra"),
    (11, 21, "Escorpio"),
    (12, 21, "Sagitario"),
    (12, 31, "Capricornio"),
]


def _zodiac(m, d):
    for zm, zd, name in ZODIAC:
        if (m, d) <= (zm, zd):
            return name
    return "Capricornio"


@bday_bp.route("/api/temporal/birthday/add", methods=["POST"])
def be_add():
    data = request.json or {}
    p = {
        "id": _state["next_id"],
        "name": data.get("name", "?"),
        "birthdate": data.get("birthdate", "2000-01-01"),
        "ts": time.time(),
    }
    _state["people"].append(p)
    _state["next_id"] += 1
    return jsonify(p)


@bday_bp.route("/api/temporal/birthday/list")
def be_list():
    now = datetime.now()
    out = []
    for p in _state["people"]:
        try:
            b = datetime.strptime(p["birthdate"], "%Y-%m-%d")
        except ValueError:
            continue
        nxt = b.replace(year=now.year)
        if nxt < now:
            nxt = nxt.replace(year=now.year + 1)
        out.append(
            {
                **p,
                "turns": nxt.year - b.year,
                "days_left": (nxt - now).days,
                "zodiac": _zodiac(b.month, b.day),
            }
        )
    return jsonify(sorted(out, key=lambda x: x["days_left"]))


@bday_bp.route("/api/temporal/birthday/delete/<int:pid>", methods=["POST"])
def be_del(pid):
    _state["people"] = [p for p in _state["people"] if p["id"] != pid]
    return jsonify({"ok": True})

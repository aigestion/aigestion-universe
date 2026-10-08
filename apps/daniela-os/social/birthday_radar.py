from datetime import datetime

from flask import Blueprint, jsonify, request

try:
    from temporal.birthday_engine import _state as _bday_state
except ImportError:
    _bday_state = {"people": []}

radar_bp = Blueprint("birthday_radar", __name__)


@radar_bp.route("/api/social/radar/upcoming")
def br_upcoming():
    days = int(request.args.get("days", 30))
    now = datetime.now()
    out = []
    for p in _bday_state.get("people", []):
        try:
            b = datetime.strptime(p["birthdate"], "%Y-%m-%d")
        except ValueError:
            continue
        nxt = b.replace(year=now.year)
        if nxt < now:
            nxt = nxt.replace(year=now.year + 1)
        left = (nxt - now).days
        if left <= days:
            out.append(
                {
                    "name": p["name"],
                    "date": nxt.strftime("%Y-%m-%d"),
                    "days_left": left,
                    "turns": nxt.year - b.year,
                }
            )
    return jsonify(sorted(out, key=lambda x: x["days_left"]))


@radar_bp.route("/api/social/radar/suggest/<name>")
def br_suggest(name):
    return jsonify(
        {
            "for": name,
            "ideas": ["carta manuscrita", "cena sorpresa", "libro dedicado"],
            "tip": "Lo que cuenta es que te acordaste a tiempo.",
        }
    )

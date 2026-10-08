from datetime import datetime

from flask import Blueprint, jsonify, request

season_bp = Blueprint("season_mood", __name__)
_state = {"custom_ritual": None}

SEASONS = [
    ("primavera", (3, 20), (6, 20), "Renacer: planta algo, limpia un cajón, estrena un hábito."),
    ("verano", (6, 21), (9, 21), "Expandir: sol, agua, encuentros, siestas sin culpa."),
    ("otoño", (9, 22), (12, 20), "Soltar: ordena, agradece, guarda energía."),
    ("invierno", (12, 21), (3, 19), "Recoger: introspección, lectura, fuego lento."),
]


def _current():
    now = datetime.now()
    md = (now.month, now.day)
    for name, start, end, _ritual in SEASONS:
        if start <= end:
            if start <= md <= end:
                return name, end
        elif md >= start or md <= end:
            return name, end
    return "invierno", (3, 19)


@season_bp.route("/api/temporal/season/now")
def se_now():
    name, end = _current()
    now = datetime.now()
    ey, em, ed = (
        (now.year + 1, end[0], end[1]) if (now.month, now.day) > end else (now.year, end[0], end[1])
    )
    days = (datetime(ey, em, ed) - now).days
    ritual = _state["custom_ritual"] or next(r for n, s, e, r in SEASONS if n == name)
    return jsonify({"season": name, "days_left": days, "ritual": ritual})


@season_bp.route("/api/temporal/season/ritual", methods=["POST"])
def se_ritual():
    data = request.json or {}
    _state["custom_ritual"] = data.get("ritual", "")
    return jsonify({"ok": True})

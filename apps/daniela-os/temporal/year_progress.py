from datetime import datetime

from flask import Blueprint, jsonify

year_bp = Blueprint("year_progress", __name__)
_state = {"views": 0}


@year_bp.route("/api/temporal/year/progress")
def yp_progress():
    now = datetime.now()
    start = datetime(now.year, 1, 1)
    end = datetime(now.year + 1, 1, 1)
    pct = round((now - start).total_seconds() / (end - start).total_seconds() * 100, 2)
    days_left = (end - now).days
    _state["views"] += 1
    bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
    return jsonify(
        {
            "year": now.year,
            "percent": pct,
            "bar": bar,
            "days_left": days_left,
            "day_of_year": now.timetuple().tm_yday,
        }
    )


@year_bp.route("/api/temporal/year/compare")
def yp_compare():
    now = datetime.now()
    pct = (now - datetime(now.year, 1, 1)).days / 365.0 * 100
    if pct < 25:
        mood = "Aún es enero mental: todo es posible."
    elif pct < 50:
        mood = "Primer tercio superado: ajusta sin culpa."
    elif pct < 75:
        mood = "Ecuador pasado: aprieta lo importante."
    else:
        mood = "Recta final: cierra bonito."
    return jsonify({"percent": round(pct, 1), "mood": mood})

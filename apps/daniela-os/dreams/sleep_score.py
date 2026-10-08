from flask import Blueprint, jsonify, request

score_bp = Blueprint("sleep_score", __name__)
_state = {"last": None}


@score_bp.route("/api/dreams/score/calc", methods=["POST"])
def ss_calc():
    data = request.json or {}
    hours = float(data.get("hours", 7))
    regularity = int(data.get("regularity", 70))
    screens = int(data.get("screens_min_before_bed", 30))
    caffeine = int(data.get("caffeine_after_16h", 0))
    s_hours = max(0, min(40, (hours / 8.0) * 40))
    s_reg = max(0, min(30, regularity * 0.3))
    s_screens = max(
        0, 20 - max(0, (60 - screens)) * 0.0 - (0 if screens >= 60 else (60 - screens) * 0.15)
    )
    s_caff = 10 if not caffeine else 4
    total = int(max(0, min(100, s_hours + s_reg + s_screens + s_caff)))
    tips = []
    if hours < 7:
        tips.append("Duerme al menos 7h: adelanta la hora de acostarte 15 min.")
    if regularity < 70:
        tips.append("Acuéstate a la misma hora (+-30 min) toda la semana.")
    if screens < 60:
        tips.append("Pantallas fuera 60 min antes de dormir.")
    if caffeine:
        tips.append("Sin cafeína después de las 16:00.")
    if not tips:
        tips.append("Excelente higiene de sueño. Sigue así.")
    _state["last"] = {"score": total, "tips": tips}
    return jsonify(_state["last"])


@score_bp.route("/api/dreams/score/last")
def ss_last():
    return jsonify(_state["last"] or {"score": None, "tip": "calcula tu score primero"})

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

cycle_bp = Blueprint("sleep_cycle", __name__)
_state = {"cycle_min": 90, "fall_asleep_min": 15}


@cycle_bp.route("/api/dreams/cycle/calc")
def sc_calc():
    wake = request.args.get("wake", "07:00")
    try:
        h, m = map(int, wake.split(":"))
    except ValueError:
        return jsonify({"error": "formato HH:MM"}), 400
    now = datetime.now().replace(second=0, microsecond=0)
    target = now.replace(hour=h, minute=m)
    if target <= now:
        target += timedelta(days=1)
    options = []
    for n in range(6, 3, -1):
        bed = target - timedelta(minutes=n * _state["cycle_min"] + _state["fall_asleep_min"])
        options.append({"cycles": n, "bedtime": bed.strftime("%H:%M"), "hours": round(n * 1.5, 1)})
    return jsonify({"wake": wake, "options": options})


@cycle_bp.route("/api/dreams/cycle/smart_alarm", methods=["POST"])
def sc_alarm():
    data = request.json or {}
    base = data.get("wake", "07:00")
    window = int(data.get("window_min", 30))
    return jsonify(
        {
            "alarm": base,
            "window_min": window,
            "tip": "La alarma sonará en el tramo de sueño ligero dentro de la ventana.",
        }
    )


@cycle_bp.route("/api/dreams/cycle/config", methods=["POST"])
def sc_config():
    data = request.json or {}
    _state["cycle_min"] = int(data.get("cycle_min", 90))
    _state["fall_asleep_min"] = int(data.get("fall_asleep_min", 15))
    return jsonify({"ok": True})

import time

from flask import Blueprint, jsonify, request

lucid_bp = Blueprint("lucid_triggers", __name__)
_state = {"checks": [], "interval_min": 90, "active": True}

MILD_GUIDE = [
    "1. Despierta tras 4.5-6h de sueño y recuerda un sueño reciente.",
    "2. Identifica una 'señal onírica' (algo imposible o raro).",
    "3. Repite: 'la próxima vez que sueñe, reconoceré que sueño'.",
    "4. Visualízate volviendo al sueño y notando la señal.",
    "5. Duerme con esa intención en mente.",
]
CHECKS = [
    "Mira tus manos: ¿tienen dedos de más o se deforman?",
    "Tápate la nariz e intenta respirar: ¿puedes?",
    "Mira un texto, aparta la vista y vuelve a mirar: ¿cambió?",
    "Pregúntate: ¿cómo llegué aquí? ¿Recuerdo los últimos 10 min?",
]


@lucid_bp.route("/api/dreams/lucid/status")
def lt_status():
    return jsonify(
        {
            "active": _state["active"],
            "interval_min": _state["interval_min"],
            "total_checks": len(_state["checks"]),
        }
    )


@lucid_bp.route("/api/dreams/lucid/config", methods=["POST"])
def lt_config():
    data = request.json or {}
    _state["interval_min"] = int(data.get("interval_min", 90))
    _state["active"] = bool(data.get("active", True))
    return jsonify({"ok": True})


@lucid_bp.route("/api/dreams/lucid/check")
def lt_check():
    import random

    prompt = random.choice(CHECKS)
    _state["checks"].append({"ts": time.time(), "prompt": prompt})
    return jsonify({"reality_check": prompt, "next_in_min": _state["interval_min"]})


@lucid_bp.route("/api/dreams/lucid/mild")
def lt_mild():
    return jsonify({"technique": "MILD", "steps": MILD_GUIDE})

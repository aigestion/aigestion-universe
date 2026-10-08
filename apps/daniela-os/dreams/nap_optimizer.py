import time

from flask import Blueprint, jsonify, request

nap_bp = Blueprint("nap_optimizer", __name__)
_state = {"last_nap": None, "history": []}

NAPS = {
    10: {
        "name": "power nap",
        "grogginess": "mínima",
        "desc": "Alerta rápida sin entrar en sueño profundo.",
    },
    20: {
        "name": "siesta clásica",
        "grogginess": "leve",
        "desc": "Descanso ideal, fácil despertar.",
    },
    90: {
        "name": "ciclo completo",
        "grogginess": "nula al completar",
        "desc": "Un ciclo entero: máxima recuperación.",
    },
}
WARN = "Evita 30-60 min: despiertas en sueño profundo (inercia del sueño)."


@nap_bp.route("/api/dreams/nap/options")
def no_options():
    return jsonify({"options": NAPS, "warning": WARN})


@nap_bp.route("/api/dreams/nap/start", methods=["POST"])
def no_start():
    data = request.json or {}
    mins = int(data.get("minutes", 20))
    info = NAPS.get(mins, {"name": "personalizada", "grogginess": "variable", "desc": ""})
    nap = {"minutes": mins, "ends_at": time.time() + mins * 60, **info}
    _state["last_nap"] = nap
    _state["history"].append(nap)
    warn = WARN if 25 <= mins <= 70 else None
    return jsonify({"nap": nap, "grogginess_warning": warn})


@nap_bp.route("/api/dreams/nap/status")
def no_status():
    if not _state["last_nap"]:
        return jsonify({"active": False})
    remaining = _state["last_nap"]["ends_at"] - time.time()
    return jsonify(
        {"active": remaining > 0, "remaining_s": max(0, int(remaining)), "nap": _state["last_nap"]}
    )

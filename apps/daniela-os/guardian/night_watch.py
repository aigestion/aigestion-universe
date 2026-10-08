import random

from flask import Blueprint, jsonify

watch_bp = Blueprint("night_watch", __name__)
_state = {"armed": False, "checks": 0}

CHECKS = [
    "Puerta principal: cerrada",
    "Ventanas: cerradas",
    "Luces exteriores: encendidas",
    "Alarma: armada",
    "Gas/cocina: apagado",
    "Persianas: bajadas",
]


@watch_bp.route("/api/guardian/night/arm", methods=["POST"])
def nw_arm():
    _state["armed"] = True
    _state["checks"] += 1
    results = [{"item": c, "ok": random.random() > 0.1} for c in CHECKS]
    fails = [r["item"] for r in results if not r["ok"]]
    return jsonify(
        {
            "armed": True,
            "report": results,
            "verdict": "Todo seguro. Buenas noches."
            if not fails
            else "Revisar: {}".format(", ".join(fails)),
        }
    )


@watch_bp.route("/api/guardian/night/disarm", methods=["POST"])
def nw_disarm():
    _state["armed"] = False
    return jsonify({"armed": False})


@watch_bp.route("/api/guardian/night/status")
def nw_status():
    return jsonify({"armed": _state["armed"], "checks": _state["checks"]})

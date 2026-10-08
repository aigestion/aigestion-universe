from flask import Blueprint, jsonify, request

noise_bp = Blueprint("white_noise", __name__)
_state = {"type": "blanco", "volume": 50, "timer_min": 0, "playing": False}

TYPES = {
    "blanco": {"desc": "Enmascara todo: ideal para bloquear ruidos.", "freq": "plano"},
    "rosa": {"desc": "Suave como lluvia: el favorito para dormir.", "freq": "1/f"},
    "marron": {"desc": "Grave y profundo: tormenta lejana.", "freq": "1/f^2"},
}


@noise_bp.route("/api/dreams/noise/status")
def wn_status():
    return jsonify(_state)


@noise_bp.route("/api/dreams/noise/set", methods=["POST"])
def wn_set():
    data = request.json or {}
    if data.get("type", "blanco") in TYPES:
        _state["type"] = data["type"]
    _state["volume"] = max(0, min(100, int(data.get("volume", 50))))
    _state["timer_min"] = max(0, int(data.get("timer_min", 0)))
    return jsonify({"ok": True})


@noise_bp.route("/api/dreams/noise/play", methods=["POST"])
def wn_play():
    _state["playing"] = True
    info = TYPES[_state["type"]]
    return jsonify(
        {
            "playing": True,
            "type": _state["type"],
            "desc": info["desc"],
            "auto_off_min": _state["timer_min"],
        }
    )


@noise_bp.route("/api/dreams/noise/stop", methods=["POST"])
def wn_stop():
    _state["playing"] = False
    return jsonify({"playing": False})

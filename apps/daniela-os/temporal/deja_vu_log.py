import time

from flask import Blueprint, jsonify, request

deja_bp = Blueprint("deja_vu_log", __name__)
_state = {"entries": [], "next_id": 1}


@deja_bp.route("/api/temporal/dejavu/log", methods=["POST"])
def dv_log():
    data = request.json or {}
    e = {
        "id": _state["next_id"],
        "cuando": data.get("cuando", ""),
        "donde": data.get("donde", ""),
        "intensidad": max(1, min(10, int(data.get("intensidad", 5)))),
        "detalle": data.get("detalle", ""),
        "ts": time.time(),
    }
    _state["entries"].append(e)
    _state["next_id"] += 1
    return jsonify(e)


@deja_bp.route("/api/temporal/dejavu/list")
def dv_list():
    return jsonify(_state["entries"])


@deja_bp.route("/api/temporal/dejavu/stats")
def dv_stats():
    n = len(_state["entries"])
    avg = round(sum(e["intensidad"] for e in _state["entries"]) / n, 1) if n else 0
    top = sorted(_state["entries"], key=lambda x: x["intensidad"], reverse=True)[:3]
    return jsonify({"total": n, "avg_intensity": avg, "top": top})

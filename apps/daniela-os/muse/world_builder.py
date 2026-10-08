import time

from flask import Blueprint, jsonify, request

world_bp = Blueprint("world_builder", __name__)
_state = {"worlds": [], "next_id": 1}


@world_bp.route("/api/muse/world/create", methods=["POST"])
def wb_create():
    data = request.json or {}
    w = {
        "id": _state["next_id"],
        "name": data.get("name", "Mundo"),
        "reglas": data.get("reglas", []),
        "mapa": data.get("mapa", ""),
        "timeline": data.get("timeline", []),
        "culturas": data.get("culturas", []),
        "ts": time.time(),
    }
    _state["worlds"].append(w)
    _state["next_id"] += 1
    return jsonify(w)


@world_bp.route("/api/muse/world/list")
def wb_list():
    return jsonify(_state["worlds"])


@world_bp.route("/api/muse/world/consistency/<int:wid>")
def wb_cons(wid):
    w = next((x for x in _state["worlds"] if x["id"] == wid), None)
    if not w:
        return jsonify({"error": "not found"}), 404
    issues = []
    if not w["reglas"]:
        issues.append("Sin reglas: define 3 leyes inviolables (magia, física, sociedad).")
    if not w["mapa"]:
        issues.append("Sin mapa: describe 3 lugares clave y cómo se viaja entre ellos.")
    if not w["culturas"]:
        issues.append("Sin culturas: ¿qué comen, qué temen, qué celebran?")
    return jsonify({"world": w["name"], "issues": issues or ["Mundo consistente. A escribir."]})

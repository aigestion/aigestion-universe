import time

from flask import Blueprint, jsonify, request

charlab_bp = Blueprint("character_lab", __name__)
_state = {"chars": [], "next_id": 1}


@charlab_bp.route("/api/muse/character/create", methods=["POST"])
def cl_create():
    data = request.json or {}
    c = {
        "id": _state["next_id"],
        "name": data.get("name", "Sin nombre"),
        "deseo": data.get("deseo", ""),
        "herida": data.get("herida", ""),
        "fantasma": data.get("fantasma", ""),
        "arco": data.get("arco", "cambio"),
        "ts": time.time(),
    }
    _state["chars"].append(c)
    _state["next_id"] += 1
    return jsonify(c)


@charlab_bp.route("/api/muse/character/list")
def cl_list():
    return jsonify(_state["chars"])


@charlab_bp.route("/api/muse/character/arc/<int:cid>")
def cl_arc(cid):
    c = next((x for x in _state["chars"] if x["id"] == cid), None)
    if not c:
        return jsonify({"error": "not found"}), 404
    return jsonify(
        {
            "name": c["name"],
            "diagnosis": "Desea '{}' pero su herida ('{}') lo frena. Su fantasma ('{}') lo persigue hasta que elige {}.".format(
                c["deseo"], c["herida"], c["fantasma"], c["arco"]
            ),
        }
    )

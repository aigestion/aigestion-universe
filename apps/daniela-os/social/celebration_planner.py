import time

from flask import Blueprint, jsonify, request

party_bp = Blueprint("celebration_planner", __name__)
_state = {"parties": [], "next_id": 1}

BASE_TASKS = [
    "Definir fecha y lugar",
    "Lista de invitados",
    "Presupuesto",
    "Comida y bebida",
    "Música/animación",
    "Confirmar asistencia",
    "Plan B lluvia",
]


@party_bp.route("/api/social/party/create", methods=["POST"])
def cp_create():
    data = request.json or {}
    budget = float(data.get("presupuesto", 200))
    guests = int(data.get("invitados", 10))
    p = {
        "id": _state["next_id"],
        "name": data.get("name", "Fiesta"),
        "budget": budget,
        "guests": guests,
        "per_person": round(budget / max(guests, 1), 2),
        "tasks": [{"t": t, "done": False} for t in BASE_TASKS],
        "ts": time.time(),
    }
    _state["parties"].append(p)
    _state["next_id"] += 1
    return jsonify(p)


@party_bp.route("/api/social/party/check/<int:pid>", methods=["POST"])
def cp_check(pid):
    data = request.json or {}
    p = next((x for x in _state["parties"] if x["id"] == pid), None)
    if not p:
        return jsonify({"error": "not found"}), 404
    for t in p["tasks"]:
        if t["t"] == data.get("task"):
            t["done"] = True
    done = sum(1 for t in p["tasks"] if t["done"])
    return jsonify({"done": done, "total": len(p["tasks"]), "tasks": p["tasks"]})


@party_bp.route("/api/social/party/list")
def cp_list():
    return jsonify(_state["parties"])

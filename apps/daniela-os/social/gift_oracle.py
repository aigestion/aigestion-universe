from flask import Blueprint, jsonify, request

gift_bp = Blueprint("gift_oracle", __name__)
_state = {"queries": 0}

IDEAS = [
    ("libro dedicado", ["lector"], 20, ["cumple", "navidad"]),
    ("planta bonita", ["hogar", "calma"], 15, ["cumple", "gracias"]),
    ("cena sorpresa", ["foodie", "pareja"], 50, ["aniversario", "cumple"]),
    ("curso online", ["curioso", "carrera"], 40, ["cumple", "graduación"]),
    ("marco con foto", ["familia", "nostálgico"], 25, ["aniversario", "navidad"]),
    ("auriculares", ["música", "tech"], 60, ["cumple", "navidad"]),
    ("experiencia spa", ["estrés", "pareja"], 70, ["aniversario", "gracias"]),
    ("juego de mesa", ["familia", "amigos"], 30, ["navidad", "cumple"]),
    ("carta manuscrita", ["nostálgico", "pareja"], 0, ["aniversario", "gracias"]),
    ("donación a su causa", ["solidario"], 25, ["cumple", "navidad"]),
]


@gift_bp.route("/api/social/gift/suggest", methods=["POST"])
def go_suggest():
    data = request.json or {}
    budget = float(data.get("presupuesto", 50))
    occasion = data.get("ocasion", "cumple").lower()
    traits = [t.lower() for t in data.get("gustos", [])]
    _state["queries"] += 1
    scored = []
    for name, tags, price, occs in IDEAS:
        if price > budget:
            continue
        score = (
            sum(2 for t in traits if t in tags)
            + (2 if occasion in occs else 0)
            + (1 if price <= budget * 0.7 else 0)
        )
        scored.append({"idea": name, "price": price, "score": score})
    return jsonify(sorted(scored, key=lambda x: x["score"], reverse=True)[:5])


@gift_bp.route("/api/social/gift/stats")
def go_stats():
    return jsonify(_state)

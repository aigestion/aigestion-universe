from flask import Blueprint, jsonify, request

soother_bp = Blueprint("nightmare_soother", __name__)
_state = {"sessions": 0}

GROUNDING = [
    "Nombra 5 cosas que VES",
    "Toca 4 cosas que SIENTES",
    "Escucha 3 sonidos",
    "Huele 2 aromas",
    "Saborea 1 cosa",
]
BREATHING = ["Inhala 4s...", "Sostén 4s...", "Exhala 6s... (repite 4 veces)"]


@soother_bp.route("/api/dreams/soother/start", methods=["POST"])
def ns_start():
    _state["sessions"] += 1
    return jsonify(
        {
            "ok": True,
            "sessions": _state["sessions"],
            "msg": "Estás a salvo. Fue solo un sueño. Vamos paso a paso.",
        }
    )


@soother_bp.route("/api/dreams/soother/grounding")
def ns_grounding():
    return jsonify({"technique": "5-4-3-2-1", "steps": GROUNDING})


@soother_bp.route("/api/dreams/soother/breathing")
def ns_breathing():
    return jsonify({"technique": "respiración calmante", "steps": BREATHING})


@soother_bp.route("/api/dreams/soother/rewrite", methods=["POST"])
def ns_rewrite():
    data = request.json or {}
    scary = data.get("nightmare", "")
    return jsonify(
        {
            "reframe": f"Imagina que '{scary[:120]}' termina bien: aparece ayuda, sale el sol, despiertas riendo. Tu cerebro aprende finales seguros."
        }
    )

from flask import Blueprint, jsonify, request

apol_bp = Blueprint("apology_helper", __name__)
_state = {"drafts": 0}

STRUCTURE = [
    "1. Nombra lo que hiciste (sin excusas).",
    "2. Reconoce el impacto en la otra persona.",
    "3. Asume responsabilidad.",
    "4. Ofrece reparar.",
    "5. Pide perdón y respeta su tiempo.",
]
EXAMPLES = {
    "leve": "“Perdona por llegar tarde, sé que te hizo esperar y eso molesta. No volverá a pasar: saldré 15 min antes. ¿Me perdonas?”",
    "media": "“Me equivoqué al decir eso delante de todos; entiendo que te avergonzó. Lo siento de verdad. ¿Cómo puedo compensarlo?”",
    "grave": "“Falté a tu confianza y sé el daño que causó. No espero que lo olvides hoy; quiero escucharte y hacer lo necesario para repararlo. Perdóname.”",
}


@apol_bp.route("/api/social/apology/guide")
def ah_guide():
    level = request.args.get("level", "media")
    return jsonify(
        {
            "structure": STRUCTURE,
            "example": EXAMPLES.get(level, EXAMPLES["media"]),
            "donts": [
                "No digas 'pero tú...'",
                "No minimices ('no fue para tanto')",
                "No exijas perdón inmediato",
            ],
        }
    )


@apol_bp.route("/api/social/apology/draft", methods=["POST"])
def ah_draft():
    data = request.json or {}
    _state["drafts"] += 1
    level = data.get("gravedad", "media")
    what = data.get("hecho", "lo que pasó")
    draft = "Perdona por {}. Entiendo que te hizo sentir mal y asumo mi parte. Quiero repararlo: {}. ¿Me perdonas?".format(
        what, data.get("reparacion", "dime qué necesitas")
    )
    return jsonify({"draft": draft, "level_example": EXAMPLES.get(level, EXAMPLES["media"])})

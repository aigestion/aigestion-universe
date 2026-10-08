import re

from flask import Blueprint, jsonify, request

dialog_bp = Blueprint("dialogue_doctor", __name__)
_state = {"diagnoses": 0}
ADVERBS = re.compile(r"\b\w+mente\b")


@dialog_bp.route("/api/muse/dialogue/diagnose", methods=["POST"])
def dd_diag():
    data = request.json or {}
    text = data.get("text", "")
    _state["diagnoses"] += 1
    adverbs = ADVERBS.findall(text)
    didas = text.count("(") + text.count("[")
    lines = [line for line in text.split("\n") if line.strip()]
    issues = []
    if adverbs:
        issues.append(
            "Adverbios en -mente: {}. Prueba verbos fuertes.".format(", ".join(adverbs[:5]))
        )
    if didas > len(lines) / 2:
        issues.append("Demasiadas didascalias: deja que el diálogo respire.")
    if lines and all(len(line) > 200 for line in lines):
        issues.append("Parlamentos largos: nadie habla 200 caracteres sin pausa.")
    return jsonify(
        {
            "adverbs": len(adverbs),
            "didascalias": didas,
            "lines": len(lines),
            "issues": issues or ["Diálogo sano."],
        }
    )


@dialog_bp.route("/api/muse/dialogue/subtext", methods=["POST"])
def dd_sub():
    data = request.json or {}
    return jsonify(
        {
            "original": data.get("text", ""),
            "subtext_tip": "Reescribe la frase diciendo lo contrario de lo que siente, pero que se note. Ej: 'estoy bien' + rompe un vaso.",
        }
    )

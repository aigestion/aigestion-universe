from flask import Blueprint, jsonify, request

scam_bp = Blueprint("scam_shield", __name__)
_state = {"checks": 0}

PATTERNS = {
    "urgencia": (
        ["urgente", "ahora mismo", "24 horas", "bloqueo", "suspend"],
        30,
        "Prisa artificial para que no pienses.",
    ),
    "premio": (
        ["premio", "ganaste", "lotería", "herencia", "millones"],
        30,
        "Si no participaste, no ganaste.",
    ),
    "autoridad": (
        ["banco", "policía", "hacienda", "juzgado", "seguridad social"],
        20,
        "Verifica por canal oficial, nunca por ese enlace.",
    ),
    "pago": (
        ["bizum", "gift card", "tarjeta regalo", "transferencia", "cripto"],
        25,
        "Pagos irreversibles = bandera roja.",
    ),
    "secreto": (
        ["no cuentes", "secreto", "solo tú", "confidencial"],
        15,
        "Aíslan a la víctima de quien la alertaría.",
    ),
}


@scam_bp.route("/api/guardian/scam/check", methods=["POST"])
def sc_check():
    data = request.json or {}
    text = data.get("text", "").lower()
    _state["checks"] += 1
    hits, score = [], 0
    for name, (words, pts, why) in PATTERNS.items():
        found = [w for w in words if w in text]
        if found:
            hits.append({"pattern": name, "matched": found, "why": why})
            score += pts
    score = min(score, 100)
    verdict = (
        "PELIGRO: probable estafa. No pagues, no pulses enlaces."
        if score >= 50
        else (
            "Sospechoso: verifica por otro canal."
            if score >= 25
            else "Sin patrones claros, mantén cautela."
        )
    )
    return jsonify({"score": score, "patterns": hits, "verdict": verdict})


@scam_bp.route("/api/guardian/scam/stats")
def sc_stats():
    return jsonify(_state)

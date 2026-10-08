from flask import Blueprint, jsonify, request

symbols_bp = Blueprint("dream_symbols", __name__)
_state = {"lookups": 0}

SYMBOLS = {
    "agua": {"es": "Emociones y fluir de la vida", "en": "Emotions and life flow"},
    "volar": {"es": "Libertad, ambición, soltar control", "en": "Freedom, ambition, letting go"},
    "dientes": {"es": "Inseguridad, imagen personal", "en": "Insecurity, self-image"},
    "casa": {"es": "El yo; cada habitación un área vital", "en": "The self; each room a life area"},
    "serpiente": {"es": "Transformación, energía oculta", "en": "Transformation, hidden energy"},
    "persecución": {"es": "Evitación de un problema", "en": "Avoiding an issue"},
    "bebé": {"es": "Nuevo comienzo, proyecto naciente", "en": "New beginning, nascent project"},
    "muerte": {"es": "Cierre de etapa, renacimiento", "en": "End of a stage, rebirth"},
    "espejo": {"es": "Autoimagen, verdad incómoda", "en": "Self-image, uncomfortable truth"},
    "lluvia": {
        "es": "Limpieza emocional, tristeza que pasa",
        "en": "Emotional cleansing, passing sadness",
    },
}


@symbols_bp.route("/api/dreams/symbols/search")
def ds_search():
    q = request.args.get("q", "").lower()
    _state["lookups"] += 1
    hits = {k: v for k, v in SYMBOLS.items() if q in k}
    return jsonify(hits)


@symbols_bp.route("/api/dreams/symbols/all")
def ds_all():
    return jsonify(SYMBOLS)


@symbols_bp.route("/api/dreams/symbols/random")
def ds_random():
    import random

    k = random.choice(list(SYMBOLS.keys()))
    return jsonify({k: SYMBOLS[k]})

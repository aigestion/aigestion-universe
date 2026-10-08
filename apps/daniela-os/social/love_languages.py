from flask import Blueprint, jsonify, request

love_bp = Blueprint("love_languages", __name__)
_state = {"profiles": {}}

LANGS = ["palabras", "tiempo", "regalos", "actos", "contacto"]
TIPS = {
    "palabras": "Di una cosa específica que admires cada día.",
    "tiempo": "Agenda 20 min de atención plena sin móvil.",
    "regalos": "Detalles pequeños e inesperados > caros.",
    "actos": "Haz una tarea suya sin que lo pida.",
    "contacto": "Abrazos de 20 segundos, mano en la mesa.",
}
QUESTIONS = [
    {
        "q": "Me siento más querido cuando...",
        "a": {
            "Me dicen algo bonito": "palabras",
            "Pasamos tiempo juntos": "tiempo",
            "Me traen un detalle": "regalos",
            "Me ayudan sin pedirlo": "actos",
            "Me abrazan": "contacto",
        },
    },
    {
        "q": "Un plan perfecto es...",
        "a": {
            "Charla profunda": "palabras",
            "Escapada juntos": "tiempo",
            "Sorpresa preparada": "regalos",
            "Cocinar juntos": "actos",
            "Cine abrazados": "contacto",
        },
    },
    {
        "q": "Lo que más me duele es...",
        "a": {
            "Críticas frías": "palabras",
            "Que no tengan tiempo": "tiempo",
            "Olvidar fechas": "regalos",
            "No ayudar nunca": "actos",
            "Frialdad física": "contacto",
        },
    },
]


@love_bp.route("/api/social/love/quiz")
def ll_quiz():
    return jsonify(QUESTIONS)


@love_bp.route("/api/social/love/answer", methods=["POST"])
def ll_answer():
    data = request.json or {}
    who = data.get("who", "yo")
    langs = [
        QUESTIONS[i]["a"].get(a, "palabras")
        for i, a in enumerate(data.get("answers", []))
        if i < len(QUESTIONS)
    ]
    top = max(set(langs), key=langs.count) if langs else "palabras"
    _state["profiles"][who] = {"top": top, "all": langs}
    return jsonify({"who": who, "language": top, "tip": TIPS[top]})


@love_bp.route("/api/social/love/couple")
def ll_couple():
    names = list(_state["profiles"].keys())
    if len(names) < 2:
        return jsonify({"tip": "Respondan el test los dos para ver compatibilidad."})
    a, b = _state["profiles"][names[0]], _state["profiles"][names[1]]
    same = a["top"] == b["top"]
    return jsonify(
        {
            "a": {names[0]: a["top"]},
            "b": {names[1]: b["top"]},
            "verdict": "¡Mismo lenguaje! Poténcienlo."
            if same
            else "Lenguajes distintos: aprendan el del otro. Tips: {} / {}".format(
                TIPS[a["top"]], TIPS[b["top"]]
            ),
        }
    )


@love_bp.route("/api/social/love/web")
def ll_web():
    cards = "".join(f"<div class='c'><h3>{k}</h3><p>{v}</p></div>" for k, v in TIPS.items())
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Love Languages</title>
<style>body{{background:#1a0a14;color:#ffd6e8;font-family:monospace;padding:30px;text-align:center}}
.c{{background:#2d0f22;border-radius:12px;padding:14px;margin:10px;display:inline-block;width:200px;vertical-align:top}}</style>
</head><body><h2>❤ Los 5 lenguajes del amor</h2>{cards}
<p>Haz el test: GET /api/social/love/quiz</p></body></html>"""

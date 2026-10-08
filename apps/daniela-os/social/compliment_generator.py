import random

from flask import Blueprint, jsonify, request

compl_bp = Blueprint("compliment_generator", __name__)
_state = {"given": 0}

COMPLIMENTS = {
    "trabajo": [
        "Tu forma de explicar lo complejo es un don.",
        "El detalle que pusiste en {x} no pasó desapercibido.",
    ],
    "amistad": [
        "Eres de esas personas que hacen que todo sea más fácil.",
        "Gracias por escuchar de verdad, no todos saben.",
    ],
    "pareja": [
        "Me encanta cómo piensas antes de hablar.",
        "Contigo hasta lo cotidiano se vuelve especial.",
    ],
    "familia": [
        "Lo que haces por esta familia sostiene más de lo que crees.",
        "Tu paciencia enseña sin decir palabra.",
    ],
    "general": [
        "Hay algo en tu energía que ordena la habitación.",
        "Se nota el cuidado que pones en lo que haces.",
    ],
}


@compl_bp.route("/api/social/compliment/make")
def cg_make():
    cat = request.args.get("cat", "general")
    about = request.args.get("about", "esto")
    pool = COMPLIMENTS.get(cat, COMPLIMENTS["general"])
    _state["given"] += 1
    return jsonify({"compliment": random.choice(pool).format(x=about), "category": cat})


@compl_bp.route("/api/social/compliment/categories")
def cg_cats():
    return jsonify(list(COMPLIMENTS.keys()))

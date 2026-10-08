import time

from flask import Blueprint, jsonify, request

freeze_bp = Blueprint("moment_freezer", __name__)
_state = {"moments": [], "next_id": 1}


@freeze_bp.route("/api/temporal/freeze/capture", methods=["POST"])
def mf_capture():
    data = request.json or {}
    m = {
        "id": _state["next_id"],
        "title": data.get("title", "Momento"),
        "emocion": data.get("emocion", ""),
        "sensorial": data.get("sensorial", ""),
        "foto_texto": data.get("foto_texto", ""),
        "ts": time.time(),
    }
    _state["moments"].append(m)
    _state["next_id"] += 1
    return jsonify(m)


@freeze_bp.route("/api/temporal/freeze/gallery")
def mf_gallery():
    return jsonify(_state["moments"])


@freeze_bp.route("/api/temporal/freeze/revisit/<int:mid>")
def mf_revisit(mid):
    m = next((x for x in _state["moments"] if x["id"] == mid), None)
    if not m:
        return jsonify({"error": "not found"}), 404
    return jsonify(
        {
            **m,
            "revisit_note": "Cierra los ojos y vuelve ahí 30 segundos. Respira ese aire otra vez.",
        }
    )


@freeze_bp.route("/api/temporal/freeze/web")
def mf_web():
    items = "".join(
        "<div class='card'><h3>{}</h3><p>❤ {}</p><p>👁 {}</p></div>".format(
            m["title"], m["emocion"], m["foto_texto"][:80]
        )
        for m in _state["moments"]
    )
    n = len(_state["moments"])
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Momentos congelados</title>
<style>body{{background:#0b1020;color:#ffe9c4;font-family:monospace;padding:30px}}
.card{{background:#16213e;border-radius:12px;padding:16px;margin:12px;max-width:500px}}</style>
</head><body><h2>❄ Momentos congelados ({n})</h2>{items or "<p>Aún no hay momentos. Congela el primero.</p>"}</body></html>"""

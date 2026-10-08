"""Brand Studio engine server — port 9920 (canonical skeleton)."""
import os

from flask import Flask, jsonify, request

from . import storyboard
from .render import ejecutar, ffmpeg, plan

SERVICE = "brand-studio"
VERSION = "1.0.0"
PORT = int(os.getenv("SERVICE_PORT", "9920"))

app = Flask(__name__)


@app.route("/api/brand/status", methods=["GET"])
def status():
    return jsonify({"status": "ok", "service": SERVICE, "version": VERSION,
                    "ffmpeg": bool(ffmpeg())})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": SERVICE})


@app.route("/api/brand/storyboard/ejemplo", methods=["GET"])
def ejemplo():
    return jsonify(storyboard.ejemplo(
        marca=request.args.get("marca", "Mi Marca"),
        estilo=request.args.get("estilo", "Cyber-Corporativo Premium")))


@app.route("/api/brand/storyboard", methods=["POST"])
def crear_storyboard():
    ok, error, norm = storyboard.validar(
        request.get_json(silent=True, force=True))
    if not ok:
        return jsonify({"ok": False, "error": error}), 400
    return jsonify({"ok": True, "storyboard": norm}), 201


@app.route("/api/brand/render", methods=["POST"])
def render():
    data = request.get_json(silent=True, force=True) or {}
    ok, error, norm = storyboard.validar(data.get("storyboard"))
    if not ok:
        return jsonify({"ok": False, "error": error}), 400
    if data.get("dry_run", True):
        return jsonify({"ok": True, "dry_run": True, "plan": plan(norm)})
    resultado = ejecutar(norm, destino=data.get("destino"))
    code = 200 if resultado.get("ok") else 503
    return jsonify(resultado), code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)

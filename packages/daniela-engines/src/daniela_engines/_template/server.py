"""Flask API server for the {{NAME}} engine.

Port {{PORT}}. Canonical skeleton — keep this shape in every engine:
  * PORT from SERVICE_PORT env (default below), never hardcoded elsewhere
  * GET /api/{{SLUG}}/status -> {"status","service","version",...}
  * GET /health -> liveness for compose healthchecks
  * app.run(host="0.0.0.0", port=PORT, debug=False) under __main__
"""
import os

from flask import Flask, jsonify

SERVICE = "{{slug}}"
VERSION = "1.0.0"
PORT = int(os.getenv("SERVICE_PORT", "{{PORT}}"))

app = Flask(__name__)


@app.route("/api/{{SLUG}}/status", methods=["GET"])
def status():
    return jsonify({"status": "ok", "service": SERVICE, "version": VERSION})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": SERVICE})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)

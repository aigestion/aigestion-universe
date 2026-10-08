# -*- coding: utf-8 -*-
import sys, os
FRONTEND_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FRONTEND_ROOT)
sys.path.insert(0, os.path.join(FRONTEND_ROOT, "shared"))

from flask import Flask, jsonify, send_from_directory
from config import WEB_PORT
from __init__ import register_frontend
from aig_shared.auth.middleware import create_auth_middleware

app = Flask(__name__, static_folder="web")
create_auth_middleware(app, public_paths={"/api/frontend/status"})
register_frontend(app)

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/api/frontend/status")
def status():
    return jsonify({"name": "Frontend Optimization", "modules": 24, "ideas": 100, "status": "alive"})

if __name__ == "__main__":
    print(f"[Frontend Opt] Starting on port {WEB_PORT}...")
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False)

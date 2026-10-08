import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERFROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, PERFROOT)

from agent_shared.config import WEB_PORT
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder="web")

def register_all():
    from async_io.async_io import async_bp
    from async_io.websocket_realtime import ws_bp
    from performance.bg_workers import worker_bp
    from performance.brotli_compression import brotli_bp
    from performance.connection_keepalive import ka_bp
    from performance.http2_server import http2_bp
    from quality.auto_formatting import fmt_bp
    from quality.ci_cd import ci_bp
    from quality.test_coverage import tc_bp
    from quality.type_hints import th_bp
    for bp in [async_bp, ws_bp, worker_bp, http2_bp, brotli_bp, ka_bp, th_bp, fmt_bp, tc_bp, ci_bp]:
        app.register_blueprint(bp)

register_all()

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/api/perf/status")
def status():
    return jsonify({"name": "Performance & Quality", "ideas": 10, "modules": 5, "status": "alive"})

if __name__ == "__main__":
    print(f"[Perf Opt] Starting on port {WEB_PORT}...")
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False)

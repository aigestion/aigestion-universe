"""
Epic PC - Web Launcher Server
Serves the launcher UI on port 5020
"""

from pathlib import Path

from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)
WEB_DIR = Path(__file__).parent


@app.route("/api/status")
def status():
    return jsonify(
        {
            "name": "Epic PC Web Launcher",
            "version": "1.0.0",
            "port": 5020,
            "status": "alive",
            "type": "ui",
        }
    )


@app.route("/")
def index():
    return send_from_directory(str(WEB_DIR), "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(str(WEB_DIR), filename)


if __name__ == "__main__":
    print("Epic PC Web Launcher starting on port 5020...")
    app.run(host="0.0.0.0", port=5020, debug=False)

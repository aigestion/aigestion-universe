"""Servidor Flask para el Dashboard 3D Unificado.

Sirve el dashboard 3D que se ve igual en PC y teléfono.
"""

import os
from pathlib import Path

try:
    from flask import Flask, jsonify, send_from_directory
except ImportError:
    Flask = None


def create_3d_dashboard_app():
    """Crea la app Flask del dashboard 3D."""
    if Flask is None:
        return None

    app = Flask(__name__)
    dashboard_dir = Path(__file__).parent

    @app.route("/")
    def index():
        return send_from_directory(dashboard_dir, "unified.html")

    @app.route("/api/live")
    def api_live():
        import psutil

        mode = "phone" if os.path.exists("/data/data/com.termux") else "pc"
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        return jsonify(
            {
                "mode": mode,
                "uptime": "24/7",
                "decisions": 0,
                "agents_active": 34,
                "agents_total": 34,
                "agents": [
                    {"name": "scout", "status": "active"},
                    {"name": "studio", "status": "idle"},
                    {"name": "social", "status": "active"},
                    {"name": "web", "status": "active"},
                    {"name": "caller", "status": "idle"},
                    {"name": "researcher", "status": "active"},
                    {"name": "guardian", "status": "active"},
                    {"name": "autonomy", "status": "active"},
                    {"name": "learning", "status": "active"},
                    {"name": "correction", "status": "active"},
                ],
                "facts": 0,
                "insights": 0,
                "recent_facts": ["Daniela está viva", "Sistema 24/7"],
                "activity_log": [
                    {"time": "22:30", "message": "Scout: 3 videos"},
                    {"time": "22:25", "message": "Studio: Video procesado"},
                ],
                "cpu": cpu,
                "ram": ram,
                "disk": disk,
                "battery": 100,
                "missions_active": 0,
                "missions": [],
                "videos_created": 0,
                "posts_published": 0,
                "views_total": 0,
                "google_services": [
                    {"name": "Gemini", "status": "active"},
                    {"name": "Firebase", "status": "active"},
                    {"name": "Colab", "status": "idle"},
                    {"name": "Chrome", "status": "active"},
                ],
                "sync_changes": 0,
                "sync_last": "Ahora",
                "sync_status": "OK",
                "tools": [
                    {"name": "code_tools", "calls": 0},
                    {"name": "content_tools", "calls": 0},
                ],
                "mcps": [
                    {"name": "code_mcp", "status": "active"},
                    {"name": "git_mcp", "status": "active"},
                ],
                "dreams_count": 0,
                "recent_dreams": ["Simulando escenarios..."],
            }
        )

    return app


if __name__ == "__main__":
    app = create_3d_dashboard_app()
    if app:
        app.run(host="0.0.0.0", port=5007, debug=False)
    else:
        print("Flask no instalado. Dashboard no disponible.")

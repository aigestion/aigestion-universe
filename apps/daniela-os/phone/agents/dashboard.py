"""Dashboard de control del ejército de agentes."""

from datetime import datetime

try:
    from flask import Flask, jsonify, render_template_string
except ImportError:
    Flask = None

from .scheduler import create_default_scheduler

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Daniela Command Center</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #eee; margin: 20px; }
        h1 { color: #00ff88; }
        .agent { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .agent h3 { color: #00ff88; margin-top: 0; }
        .status-running { color: #00ff88; }
        .status-idle { color: #ffaa00; }
        .status-error { color: #ff4444; }
        .metrics { color: #888; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>🧠 Daniela Command Center</h1>
    <p>Última actualización: {{ timestamp }}</p>
    <p>Estado: <span class="status-{{ 'running' if status.running else 'idle' }}">{{ 'ACTIVO' if status.running else 'DETENIDO' }}</span></p>

    <h2>Agentes</h2>
    {% for name, agent in status.agents.items() %}
    <div class="agent">
        <h3>{{ name }}</h3>
        <p>Estado: <span class="status-{{ agent.status }}">{{ agent.status }}</span></p>
        <p>Última ejecución: {{ agent.last_run or 'Nunca' }}</p>
        <p class="metrics">
            Ejecuciones: {{ agent.metrics.runs }} |
            Éxitos: {{ agent.metrics.success }} |
            Errores: {{ agent.metrics.errors }}
        </p>
        <p class="metrics">Último output: {{ agent.metrics.last_output or 'N/A' }}</p>
    </div>
    {% endfor %}
</body>
</html>
"""


def create_dashboard_app():
    """Crea la app Flask del dashboard."""
    if Flask is None:
        return None

    app = Flask(__name__)
    scheduler = create_default_scheduler()

    @app.route("/")
    def index():
        status = scheduler.get_status()
        return render_template_string(
            DASHBOARD_HTML,
            status=status,
            timestamp=datetime.now().isoformat(),
        )

    @app.route("/api/status")
    def api_status():
        return jsonify(scheduler.get_status())

    @app.route("/api/start")
    def start():
        scheduler.start()
        return jsonify({"status": "started"})

    @app.route("/api/stop")
    def stop():
        scheduler.stop()
        return jsonify({"status": "stopped"})

    return app


if __name__ == "__main__":
    app = create_dashboard_app()
    if app:
        app.run(host="0.0.0.0", port=5001, debug=False)
    else:
        print("Flask no instalado. Dashboard no disponible.")

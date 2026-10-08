"""Dashboard de Tools.

Visualiza qué tools se usan más y su estado.
"""

from datetime import datetime
from typing import Any

try:
    from flask import Flask, jsonify, render_template_string
except ImportError:
    Flask = None

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Daniela Tools Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #eee; margin: 20px; }
        h1 { color: #00ff88; }
        .tool { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .tool h3 { color: #00ff88; margin-top: 0; }
        .metric { color: #00ff88; font-size: 1.2em; }
        .label { color: #888; }
    </style>
</head>
<body>
    <h1>🔧 Daniela Tools Dashboard</h1>
    <p>Última actualización: {{ timestamp }}</p>

    <h2>Tools Disponibles</h2>
    {% for tool in tools %}
    <div class="tool">
        <h3>{{ tool.name }}</h3>
        <p><span class="label">Categoría:</span> {{ tool.category }}</p>
        <p><span class="label">Funciones:</span> {{ tool.functions }}</p>
        <p><span class="label">Estado:</span> <span class="metric">{{ tool.status }}</span></p>
    </div>
    {% endfor %}

    <h2>Estadísticas</h2>
    <div class="tool">
        <p><span class="label">Total tools:</span> <span class="metric">{{ total_tools }}</span></p>
        <p><span class="label">Total funciones:</span> <span class="metric">{{ total_functions }}</span></p>
    </div>
</body>
</html>
"""


def get_tools_info() -> list[dict[str, Any]]:
    """Obtiene información de todos los tools."""
    tools = [
        {"name": "code_tools", "category": "Código", "functions": 4, "status": "activo"},
        {"name": "git_tools", "category": "Git", "functions": 3, "status": "activo"},
        {"name": "system_tools", "category": "Sistema", "functions": 4, "status": "activo"},
        {"name": "content_tools", "category": "Contenido", "functions": 5, "status": "activo"},
        {"name": "social_tools", "category": "Redes", "functions": 4, "status": "activo"},
        {"name": "ai_tools", "category": "IA", "functions": 4, "status": "activo"},
    ]
    return tools


def create_tools_dashboard_app():
    """Crea la app Flask del dashboard de tools."""
    if Flask is None:
        return None

    app = Flask(__name__)

    @app.route("/")
    def index():
        tools = get_tools_info()
        return render_template_string(
            DASHBOARD_HTML,
            timestamp=datetime.now().isoformat(),
            tools=tools,
            total_tools=len(tools),
            total_functions=sum(t["functions"] for t in tools),
        )

    @app.route("/api/tools")
    def api_tools():
        return jsonify(get_tools_info())

    return app


if __name__ == "__main__":
    app = create_tools_dashboard_app()
    if app:
        app.run(host="0.0.0.0", port=5003, debug=False)
    else:
        print("Flask no instalado. Dashboard no disponible.")

"""Dashboard Unificado de Todo.

Un solo dashboard con tabs para Agentes, Tools, MCPs, Skills, Tests, Métricas.
"""

from datetime import datetime

try:
    from flask import Flask, jsonify, render_template_string
except ImportError:
    Flask = None

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Daniela Unified Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #eee; margin: 20px; }
        h1 { color: #00ff88; }
        h2 { color: #00ccff; }
        .tab { display: inline-block; padding: 10px 20px; background: #16213e; margin: 5px; cursor: pointer; border-radius: 5px; }
        .tab.active { background: #00ff88; color: #000; }
        .content { display: none; }
        .content.active { display: block; }
        .card { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .metric { color: #00ff88; font-size: 1.2em; }
        .label { color: #888; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #333; }
        th { color: #00ff88; }
    </style>
</head>
<body>
    <h1>🧠 Daniela Unified Dashboard</h1>
    <p>Última actualización: {{ timestamp }}</p>

    <div>
        <span class="tab active" onclick="showTab('agents')">Agentes</span>
        <span class="tab" onclick="showTab('tools')">Tools</span>
        <span class="tab" onclick="showTab('mcps')">MCPs</span>
        <span class="tab" onclick="showTab('skills')">Skills</span>
        <span class="tab" onclick="showTab('tests')">Tests</span>
        <span class="tab" onclick="showTab('metrics')">Métricas</span>
    </div>

    <div id="agents" class="content active">
        <h2>Agentes</h2>
        {% for agent in agents %}
        <div class="card">
            <h3>{{ agent.name }}</h3>
            <p><span class="label">Estado:</span> <span class="metric">{{ agent.status }}</span></p>
            <p><span class="label">Ejecuciones:</span> {{ agent.metrics.runs }}</p>
            <p><span class="label">Éxitos:</span> {{ agent.metrics.success }}</p>
            <p><span class="label">Errores:</span> {{ agent.metrics.errors }}</p>
        </div>
        {% endfor %}
    </div>

    <div id="tools" class="content">
        <h2>Tools</h2>
        {% for tool in tools %}
        <div class="card">
            <h3>{{ tool.name }}</h3>
            <p><span class="label">Categoría:</span> {{ tool.category }}</p>
            <p><span class="label">Funciones:</span> {{ tool.functions }}</p>
        </div>
        {% endfor %}
    </div>

    <div id="mcps" class="content">
        <h2>MCPs</h2>
        {% for mcp in mcps %}
        <div class="card">
            <h3>{{ mcp.name }}</h3>
            <p><span class="label">Tools:</span> {{ mcp.tools }}</p>
        </div>
        {% endfor %}
    </div>

    <div id="skills" class="content">
        <h2>Skills</h2>
        {% for skill in skills %}
        <div class="card">
            <h3>{{ skill.name }}</h3>
            <p><span class="label">Capacidades:</span> {{ skill.capabilities }}</p>
        </div>
        {% endfor %}
    </div>

    <div id="tests" class="content">
        <h2>Tests</h2>
        <div class="card">
            <p><span class="label">Total tests:</span> <span class="metric">{{ tests.total }}</span></p>
            <p><span class="label">Passing:</span> <span class="metric">{{ tests.passing }}</span></p>
            <p><span class="label">Failing:</span> <span class="metric">{{ tests.failing }}</span></p>
        </div>
    </div>

    <div id="metrics" class="content">
        <h2>Métricas</h2>
        <div class="card">
            <p><span class="label">Uptime:</span> {{ metrics.uptime }}</p>
            <p><span class="label">CPU:</span> {{ metrics.cpu }}%</p>
            <p><span class="label">RAM:</span> {{ metrics.ram }}%</p>
            <p><span class="label">Disco:</span> {{ metrics.disk }}%</p>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            document.querySelectorAll('.content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""


def create_unified_dashboard_app():
    """Crea la app Flask del dashboard unificado."""
    if Flask is None:
        return None

    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(
            DASHBOARD_HTML,
            timestamp=datetime.now().isoformat(),
            agents=[],
            tools=[],
            mcps=[],
            skills=[],
            tests={"total": 0, "passing": 0, "failing": 0},
            metrics={"uptime": "24/7", "cpu": "0%", "ram": "0%", "disk": "0%"},
        )

    @app.route("/api/status")
    def api_status():
        return jsonify(
            {
                "agents": [],
                "tools": [],
                "mcps": [],
                "skills": [],
                "tests": {"total": 0, "passing": 0, "failing": 0},
                "metrics": {"uptime": "24/7", "cpu": "0%", "ram": "0%", "disk": "0%"},
            }
        )

    return app


if __name__ == "__main__":
    app = create_unified_dashboard_app()
    if app:
        app.run(host="0.0.0.0", port=5004, debug=False)
    else:
        print("Flask no instalado. Dashboard no disponible.")

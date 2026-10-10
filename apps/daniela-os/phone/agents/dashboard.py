"""Daniela OS Dashboard — panel unificado de control.

Consolida el Command Center de agentes con los datos de:
- core.dashboard       -> /api/dashboard/services (18 servicios OS)
- tools_dashboard      -> get_tools_info()
- live_dashboard       -> get_live_data() (psutil: CPU/RAM/disk/battery, MCPs, agentes)
- scheduler            -> get_status() (ejército de agentes)

Reemplaza al antiguo dashboard unificado (vacío) y unifica los endpoints
dispersos en los puertos 5001/5003/5004/5006: ahora todo está en el puerto 5001
como "Daniela OS Dashboard".
"""

import glob
from datetime import datetime
from pathlib import Path

try:
    from flask import Flask, jsonify, render_template_string
except ImportError:
    Flask = None



DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Daniela OS Dashboard</title>
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
        .agent { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .agent h3 { color: #00ff88; margin-top: 0; }
        .status-running { color: #00ff88; }
        .status-idle { color: #ffaa00; }
        .status-error { color: #ff4444; }
        .status-offline { color: #888; }
        .metrics { color: #888; font-size: 0.9em; }
        .note { color: #f0ad4e; }
    </style>
</head>
<body>
    <h1>🧠 Daniela OS Dashboard</h1>
    <p>Última actualización: {{ timestamp }}</p>
    <p>Estado: <span class="status-{{ 'running' if status.running else 'idle' }}">{{ 'ACTIVO' if status.running else 'DETENIDO' }}</span></p>

    <div>
        <span class="tab active" onclick="showTab('agentes')">Agentes</span>
        <span class="tab" onclick="showTab('servicios')">Servicios</span>
        <span class="tab" onclick="showTab('tools')">Tools</span>
        <span class="tab" onclick="showTab('mcps')">MCPs</span>
        <span class="tab" onclick="showTab('skills')">Skills</span>
        <span class="tab" onclick="showTab('tests')">Tests</span>
        <span class="tab" onclick="showTab('metricas')">Métricas</span>
    </div>

    <!-- TAB AGENTES -->
    <div id="agentes" class="content active">
        <h2>🤖 Ejército de Agentes</h2>
        {% if scheduler_error %}
        <p class="note">⚠️ No se pudo cargar el scheduler (modo standalone): {{ scheduler_error }}</p>
        {% else %}
        {% for name, agent in status.agents.items() %}
        <div class="agent">
            <h3>{{ name }}</h3>
            <p>Estado: <span class="status-{{ agent.status }}">{{ agent.status }}</span></p>
            <p>Última ejecución: {{ agent.last_run or 'Nunca' }}</p>
            <p class="metrics">Ejecuciones: {{ agent.metrics.runs }} | Éxitos: {{ agent.metrics.success }} | Errores: {{ agent.metrics.errors }}</p>
            <p class="metrics">Último output: {{ agent.metrics.last_output or 'N/A' }}</p>
        </div>
        {% endfor %}
        {% endif %}
    </div>

    <!-- TAB SERVICIOS -->
    <div id="servicios" class="content">
        <h2>🌐 Servicios OS (18 motores)</h2>
        {% if services %}
        <p class="label">Online: {{ services.summary.online }} | Offline: {{ services.summary.offline }} | Total: {{ services.summary.total }}</p>
        <table>
            <tr><th>Motor</th><th>Categoría</th><th>Puerto</th><th>Estado</th></tr>
            {% for svc in services.services %}
            <tr>
                <td>{{ svc.name }}</td>
                <td>{{ svc.category }}</td>
                <td>{{ svc.port }}</td>
                <td><span class="{{ 'status-running' if svc.status == 'online' else 'status-offline' }}">{{ svc.status }}</span></td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p class="note">No se pudo contactar con el servidor OS en :9200 (el dashboard puede ejecutarse en modo standalone).</p>
        {% endif %}
    </div>

    <!-- TAB TOOLS -->
    <div id="tools" class="content">
        <h2>🔧 Tools</h2>
        {% if tools %}
        <table>
            <tr><th>Tool</th><th>Categoría</th><th>Funciones</th><th>Estado</th></tr>
            {% for tool in tools %}
            <tr>
                <td>{{ tool.name }}</td>
                <td>{{ tool.category }}</td>
                <td>{{ tool.functions }}</td>
                <td>{{ tool.status }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p class="note">Ninguna tool registrada.</p>
        {% endif %}
    </div>

    <!-- TAB MCPs -->
    <div id="mcps" class="content">
        <h2>🔌 MCPs (Model Context Protocol)</h2>
        {% if mcps %}
        <table>
            <tr><th>MCP</th><th>Estado</th></tr>
            {% for mcp in mcps %}
            <tr>
                <td>{{ mcp.name }}</td>
                <td><span class="{{ 'status-running' if mcp.status == 'active' else 'status-idle' }}">{{ mcp.status }}</span></td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p class="note">Ningún MCP detectado.</p>
        {% endif %}
    </div>

    <!-- TAB SKILLS -->
    <div id="skills" class="content">
        <h2>💡 Skills</h2>
        <p class="note">No existe un registry centralizado de Skills detectado en este repo. (Inventario manual: ver daniela_v7_advanced.py / personalidad.)</p>
    </div>

    <!-- TAB TESTS -->
    <div id="tests" class="content">
        <h2>✅ Tests</h2>
        <p class="label">Tests descubiertos en tests/: {{ tests.count }}</p>
    </div>

    <!-- TAB MÉTRICAS -->
    <div id="metricas" class="content">
        <h2>🖥️ Métricas del Sistema</h2>
        <table>
            <tr><th>Recurso</th><th>Uso</th></tr>
            <tr><td>CPU</td><td><span class="metric">{{ metrics.cpu }}%</span></td></tr>
            <tr><td>RAM</td><td><span class="metric">{{ metrics.ram }}%</span></td></tr>
            <tr><td>Disco</td><td><span class="metric">{{ metrics.disk }}%</span></td></tr>
            <tr><td>Batería</td><td><span class="metric">{{ metrics.battery }}%</span></td></tr>
            <tr><td>Uptime</td><td><span class="metric">{{ metrics.uptime }}</span></td></tr>
        </table>
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


def get_services_status():
    """Obtiene el estado de los 18 servicios del OS."""
    try:
        from core.dashboard import get_all_status
        return get_all_status()
    except Exception:
        pass
    try:
        import json
        import urllib.request
        req = urllib.request.Request("http://localhost:9200/api/dashboard/services")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        pass
    return None


def get_tools_info():
    try:
        from .tools_dashboard import get_tools_info as _get_tools
        return _get_tools()
    except Exception:
        return []


def get_mcps():
    try:
        from .live_dashboard import get_live_data
        return get_live_data().get("mcps", [])
    except Exception:
        return []


def get_system_metrics():
    try:
        from .live_dashboard import get_live_data
        ld = get_live_data()
        return {
            "cpu": ld.get("cpu", "N/A"),
            "ram": ld.get("ram", "N/A"),
            "disk": ld.get("disk", "N/A"),
            "battery": ld.get("battery", "N/A"),
            "uptime": ld.get("uptime", "N/A"),
        }
    except Exception:
        return {"cpu": "N/A", "ram": "N/A", "disk": "N/A", "battery": "N/A", "uptime": "N/A"}


def get_tests_count():
    base = Path(__file__).resolve().parent.parent.parent.parent.parent
    tests_dir = base / "tests"
    files = glob.glob(str(tests_dir / "**" / "test_*.py"), recursive=True)
    return len(files)


def create_dashboard_app():
    """Crea la app Flask del dashboard unificado Daniela OS."""
    if Flask is None:
        return None

    app = Flask(__name__)
    try:
        from .scheduler import create_default_scheduler
        try:
            scheduler = create_default_scheduler()
            scheduler_error = None
        except Exception as e:
            scheduler = None
            scheduler_error = f"{type(e).__name__}: {e}"
    except Exception as e:
        scheduler = None
        scheduler_error = f"module load: {type(e).__name__}: {e}"

    def gather_data():
        if scheduler is None:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": {"running": False, "agents": {}},
                "services": get_services_status(),
                "tools": get_tools_info(),
                "mcps": get_mcps(),
                "tests": {"count": get_tests_count(), "recent": None},
                "metrics": get_system_metrics(),
                "scheduler_error": scheduler_error,
            }
        status = scheduler.get_status()
        return {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "services": get_services_status(),
            "tools": get_tools_info(),
            "mcps": get_mcps(),
            "tests": {"count": get_tests_count(), "recent": None},
            "metrics": get_system_metrics(),
            "scheduler_error": None,
        }

    @app.route("/")
    def index():
        data = gather_data()
        return render_template_string(DASHBOARD_HTML, **data)

    @app.route("/api/status")
    def api_status():
        data = gather_data()
        if data["scheduler_error"]:
            return jsonify({"running": False, "agents": {}, "scheduler_error": data["scheduler_error"]})
        status = data["status"]
        result = {
            "running": status.running,
            "agents": status.agents,
        }
        services = data["services"]
        if services:
            result["services_online"] = services["summary"]["online"]
            result["services_total"] = services["summary"]["total"]
        result["tools"] = len(data["tools"])
        result["mcps"] = len(data["mcps"])
        result["tests"] = data["tests"]["count"]
        result["metrics"] = data["metrics"]
        return jsonify(result)

    @app.route("/api/start")
    def start():
        if scheduler is None:
            return jsonify({"status": "error", "message": "scheduler no disponible (modo standalone)"}), 503
        scheduler.start()
        return jsonify({"status": "started"})

    @app.route("/api/stop")
    def stop():
        if scheduler is None:
            return jsonify({"status": "error", "message": "scheduler no disponible (modo standalone)"}), 503
        scheduler.stop()
        return jsonify({"status": "stopped"})

    return app


if __name__ == "__main__":
    app = create_dashboard_app()
    if app:
        app.run(host="0.0.0.0", port=5001, debug=False)
    else:
        print("Flask no instalado. Dashboard no disponible.")

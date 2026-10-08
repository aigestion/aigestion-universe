"""Dashboard Vivo de Daniela.

Múltiples frames en un solo dashboard que muestran a Daniela "viva".
Funciona igual en teléfono (Termux) y PC (Docker).
"""

import os
from typing import Any

try:
    from flask import Flask, jsonify, render_template_string
    from flask_socketio import SocketIO
except ImportError:
    Flask = None
    SocketIO = None

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Daniela Live Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', monospace;
            background: #0a0a1a;
            color: #eee;
            overflow: hidden;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: repeat(3, 1fr);
            gap: 10px;
            height: 100vh;
            padding: 10px;
        }
        .frame {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #333;
            border-radius: 12px;
            padding: 15px;
            overflow: hidden;
            position: relative;
            transition: all 0.3s ease;
        }
        .frame:hover {
            border-color: #00ff88;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
        }
        .frame-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }
        .frame-title {
            color: #00ff88;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .frame-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00ff88;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .frame-content {
            font-size: 12px;
            line-height: 1.6;
        }
        .metric {
            color: #00ff88;
            font-size: 24px;
            font-weight: bold;
        }
        .label {
            color: #888;
            font-size: 11px;
        }
        .status-active { color: #00ff88; }
        .status-idle { color: #ffaa00; }
        .status-error { color: #ff4444; }
        .bar {
            height: 6px;
            background: #333;
            border-radius: 3px;
            margin: 5px 0;
            overflow: hidden;
        }
        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00ccff);
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        .log-entry {
            padding: 3px 0;
            border-bottom: 1px solid #222;
            font-size: 11px;
        }
        .log-time { color: #666; }
        .agent-item {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #222;
        }
        .mission-item {
            padding: 5px;
            background: #0a0a1a;
            border-radius: 5px;
            margin: 5px 0;
            border-left: 3px solid #00ff88;
        }
        .brain-fact {
            padding: 5px;
            background: #0a0a1a;
            border-radius: 5px;
            margin: 5px 0;
            font-size: 11px;
        }
        .pulse-text {
            animation: pulse-text 2s infinite;
        }
        @keyframes pulse-text {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .glow {
            text-shadow: 0 0 10px #00ff88;
        }
    </style>
</head>
<body>
    <div class="grid">
        <!-- Frame 1: Estado de Daniela -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🧠 Daniela</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                <p class="metric glow">VIVA</p>
                <p class="label">Estado: <span class="status-active">Activa</span></p>
                <p class="label">Modo: {{ mode }}</p>
                <p class="label">Uptime: {{ uptime }}</p>
                <p class="label">Decisiones: {{ decisions }}</p>
            </div>
        </div>

        <!-- Frame 2: Agentes -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🤖 Agentes</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                <p class="metric">{{ agents_active }}/{{ agents_total }}</p>
                <p class="label">Agentes activos</p>
                {% for agent in agents %}
                <div class="agent-item">
                    <span>{{ agent.name }}</span>
                    <span class="status-{{ agent.status }}">{{ agent.status }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Frame 3: Cerebro -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">💡 Cerebro</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                <p class="metric">{{ facts }}</p>
                <p class="label">Hechos</p>
                <p class="metric">{{ insights }}</p>
                <p class="label">Insights</p>
                {% for fact in recent_facts %}
                <div class="brain-fact">{{ fact }}</div>
                {% endfor %}
            </div>
        </div>

        <!-- Frame 4: Actividad -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">📊 Actividad</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                {% for log in activity_log %}
                <div class="log-entry">
                    <span class="log-time">{{ log.time }}</span>
                    <span>{{ log.message }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Frame 5: Sistema -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">💻 Sistema</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                <p class="label">CPU</p>
                <div class="bar"><div class="bar-fill" style="width: {{ cpu }}%"></div></div>
                <p class="label">RAM</p>
                <div class="bar"><div class="bar-fill" style="width: {{ ram }}%"></div></div>
                <p class="label">Disco</p>
                <div class="bar"><div class="bar-fill" style="width: {{ disk }}%"></div></div>
                <p class="label">Batería</p>
                <div class="bar"><div class="bar-fill" style="width: {{ battery }}%"></div></div>
            </div>
        </div>

        <!-- Frame 6: Misiones -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🎯 Misiones</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                <p class="metric">{{ missions_active }}</p>
                <p class="label">Activas</p>
                {% for mission in missions %}
                <div class="mission-item">
                    <strong>{{ mission.name }}</strong>
                    <span class="label">{{ mission.objective }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Frame 7: Contenido -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🎬 Contenido</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                <p class="metric">{{ videos_created }}</p>
                <p class="label">Videos creados</p>
                <p class="metric">{{ posts_published }}</p>
                <p class="label">Posts publicados</p>
                <p class="metric">{{ views_total }}</p>
                <p class="label">Views totales</p>
            </div>
        </div>

        <!-- Frame 8: Google -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🔮 Google</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                {% for service in google_services %}
                <div class="agent-item">
                    <span>{{ service.name }}</span>
                    <span class="status-{{ service.status }}">{{ service.status }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Frame 9: Sync -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🔄 Sync</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                <p class="metric">{{ sync_changes }}</p>
                <p class="label">Cambios pendientes</p>
                <p class="metric">{{ sync_last }}</p>
                <p class="label">Última sync</p>
                <p class="label">Teléfono ↔ PC</p>
                <div class="bar"><div class="bar-fill" style="width: {{ sync_status }}%"></div></div>
            </div>
        </div>

        <!-- Frame 10: Tools -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🔧 Tools</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                {% for tool in tools %}
                <div class="agent-item">
                    <span>{{ tool.name }}</span>
                    <span class="metric">{{ tool.calls }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Frame 11: MCPs -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🔌 MCPs</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                {% for mcp in mcps %}
                <div class="agent-item">
                    <span>{{ mcp.name }}</span>
                    <span class="status-{{ mcp.status }}">{{ mcp.status }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Frame 12: Dream -->
        <div class="frame">
            <div class="frame-header">
                <span class="frame-title">🌙 Dream</span>
                <span class="frame-status"></span>
            </div>
            <div class="frame-content">
                <p class="metric">{{ dreams_count }}</p>
                <p class="label">Sueños simulados</p>
                {% for dream in recent_dreams %}
                <div class="brain-fact">{{ dream }}</div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""


def get_live_data() -> dict[str, Any]:
    """Obtiene datos en vivo para el dashboard."""
    import psutil

    # Detectar modo
    mode = "phone" if os.path.exists("/data/data/com.termux") else "pc"

    # Recursos del sistema
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    battery = 100
    try:
        bat = psutil.sensors_battery()
        if bat:
            battery = bat.percent
    except Exception:
        pass

    # Datos simulados (en producción vendrían de los agentes reales)
    return {
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
        "recent_facts": [
            "Daniela está viva",
            "Sistema operativo 24/7",
            "Todos los agentes activos",
        ],
        "activity_log": [
            {"time": "22:30", "message": "Scout: 3 videos descubiertos"},
            {"time": "22:25", "message": "Studio: Video procesado"},
            {"time": "22:20", "message": "Social: 5 posts publicados"},
            {"time": "22:15", "message": "Guardian: Backup completado"},
            {"time": "22:10", "message": "Learning: +10 insights"},
        ],
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "battery": battery,
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
        "sync_status": 100,
        "tools": [
            {"name": "code_tools", "calls": 0},
            {"name": "content_tools", "calls": 0},
            {"name": "social_tools", "calls": 0},
            {"name": "ai_tools", "calls": 0},
        ],
        "mcps": [
            {"name": "code_mcp", "status": "active"},
            {"name": "git_mcp", "status": "active"},
            {"name": "ai_mcp", "status": "active"},
        ],
        "dreams_count": 0,
        "recent_dreams": [
            "Simulando escenarios...",
            "Planificando misiones...",
        ],
    }


def create_live_dashboard_app():
    """Crea la app Flask del dashboard vivo."""
    if Flask is None:
        return None

    app = Flask(__name__)

    @app.route("/")
    def index():
        data = get_live_data()
        return render_template_string(DASHBOARD_HTML, **data)

    @app.route("/api/live")
    def api_live():
        return jsonify(get_live_data())

    return app


if __name__ == "__main__":
    app = create_live_dashboard_app()
    if app:
        app.run(host="0.0.0.0", port=5006, debug=False)
    else:
        print("Flask no instalado. Dashboard no disponible.")

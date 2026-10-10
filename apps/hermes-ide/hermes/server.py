import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERMES_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, HERMES_ROOT)
sys.path.insert(0, os.path.join(HERMES_ROOT, "integration"))
sys.path.insert(0, os.path.join(HERMES_ROOT, "skills"))
sys.path.insert(0, os.path.join(HERMES_ROOT, "memory"))
sys.path.insert(0, os.path.join(HERMES_ROOT, "automation"))
sys.path.insert(0, os.path.join(HERMES_ROOT, "personality"))
sys.path.insert(0, os.path.join(HERMES_ROOT, "advanced"))
sys.path.insert(0, os.path.join(BASE, "aig-optimization"))
sys.path.insert(0, os.path.join(BASE, "aig-optimization", "cache"))
sys.path.insert(0, os.path.join(BASE, "aig-optimization", "sse"))
sys.path.insert(0, os.path.join(BASE, "aig-optimization", "health"))
sys.path.insert(0, os.path.join(BASE, "aig-optimization", "observe"))
sys.path.insert(0, os.path.join(BASE, "aig-optimization", "conn"))

from agent_shared.config import WEB_PORT
from flask import Flask, jsonify, send_from_directory

from core.auth.casbin_auth import create_auth_middleware
from core.message_broker import Event, get_in_memory_bus
from core.service_registry import register_service, update_heartbeat

app = Flask(__name__, static_folder="web")
create_auth_middleware(app)

# Event bus
event_bus = get_in_memory_bus("hermes")

def _try_opt(name):
    """Import + register one optimization blueprint; skip if unavailable (e.g. slim container)."""
    try:
        mod = __import__(name)
        bp = getattr(mod, [n for n in dir(mod) if n.endswith("_bp")][0])
        app.register_blueprint(bp)
    except Exception as e:
        print(f"[Hermes] Optional blueprint '{name}' skipped: {e}")

def register_all():
    from advanced import register_advanced
    from automation import register_automation
    from integration import register_integration
    from memory import register_memory
    from personality import register_personality

    from skills import register_skills
    register_integration(app)
    register_skills(app)
    register_memory(app)
    register_automation(app)
    register_personality(app)
    register_advanced(app)
    for mod in ["sse_server", "health_checker", "observability", "connection_pool"]:
        _try_opt(mod)

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/api/status")
def status():
    return jsonify({
        "name": "Hermes",
        "version": "1.0.0",
        "modules": 70,
        "phases": ["Integration", "Skills", "Memory", "Automation", "Personality", "Advanced", "Optimization"],
        "optimizations": ["Redis Caching", "SSE", "Health Checks", "Observability", "Connection Pooling"],
        "status": "alive",
        "total_ideas": 50,
        "registry": "active",
        "events": "active"
    })

@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    update_heartbeat("hermes")
    return jsonify({"status": "ok"})

register_all()

if __name__ == "__main__":
    # Register with service registry
    register_service(
        name="hermes",
        host="0.0.0.0",
        port=WEB_PORT,
        category="AI",
        version="1.0.0",
        endpoints=["/api/status", "/api/integration", "/api/skills", "/api/memory"]
    )

    # Publish startup event
    event = Event(type="service.startup", payload={"service": "hermes", "port": WEB_PORT}, source="hermes")
    event_bus.publish_sync("startup", event)

    print(f"[Hermes] Starting on port {WEB_PORT}...")
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False)

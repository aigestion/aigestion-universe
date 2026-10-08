

from .cross_agent_delegation import delegation_bp
from .hermes_daniela_bridge import bridge_bp
from .shared_memory_sync import memory_sync_bp
from .unified_dashboard import unified_dash_bp
from .voice_engine import voice_engine_bp


def register_integration(app):
    for bp in [bridge_bp, memory_sync_bp, voice_engine_bp, delegation_bp, unified_dash_bp]:
        app.register_blueprint(bp)

from .attention_awareness import attention_bp
from .conflict_resolution import conflict_bp
from .context_handoff import handoff_bp
from .cross_routines import routines_bp
from .device_handoff import device_handoff_bp
from .memory_graph import memory_bp
from .parallel_processing import parallel_bp
from .shared_focus import focus_bp
from .split_consciousness import split_bp
from .unified_personality import personality_bp


def register_consciousness(app):
    for bp in [
        memory_bp,
        handoff_bp,
        attention_bp,
        routines_bp,
        split_bp,
        focus_bp,
        device_handoff_bp,
        parallel_bp,
        conflict_bp,
        personality_bp,
    ]:
        app.register_blueprint(bp)

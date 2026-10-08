from .anomaly_alerts import anomaly_bp
from .auto_organization import auto_org_bp
from .contextual_suggestions import suggestions_bp
from .duplicate_detection import dup_bp
from .energy_management import energy_bp
from .habit_nudges import nudges_bp
from .meeting_predictor import meeting_bp
from .pattern_learning import pattern_bp
from .predictive_preload import preload_bp
from .smart_interruptions import smart_interrupt_bp


def register_proactive(app):
    for bp in [
        preload_bp,
        smart_interrupt_bp,
        suggestions_bp,
        auto_org_bp,
        nudges_bp,
        meeting_bp,
        energy_bp,
        dup_bp,
        pattern_bp,
        anomaly_bp,
    ]:
        app.register_blueprint(bp)

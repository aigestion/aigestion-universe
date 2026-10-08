

from .celebration_mode import celebration_bp
from .communication_style import comm_bp
from .contextual_jokes import jokes_bp
from .empathy_engine import empathy_bp
from .growth_tracking import growth_track_bp
from .humor_system import humor_bp
from .learning_style import learning_bp
from .mood_detection import mood_detect_bp
from .preference_memory import pref_bp
from .proactive_suggestions import proactive_sugg_bp


def register_personality(app):
    for bp in [mood_detect_bp, humor_bp, empathy_bp, celebration_bp, learning_bp, comm_bp, pref_bp, proactive_sugg_bp, jokes_bp, growth_track_bp]:
        app.register_blueprint(bp)

from .achievement_celebration import celebration_bp
from .comfort_mode import comfort_bp
from .emotional_journaling import journal_bp
from .growth_tracking import growth_bp
from .inside_jokes import inside_jokes_bp
from .legacy_builder import legacy_bp
from .memory_lane import memory_lane_bp
from .mood_mirror import mood_bp
from .shared_secrets import secrets_bp
from .voice_personality import voice_personality_bp


def register_emotional(app):
    for bp in [
        mood_bp,
        memory_lane_bp,
        celebration_bp,
        journal_bp,
        voice_personality_bp,
        inside_jokes_bp,
        growth_bp,
        comfort_bp,
        secrets_bp,
        legacy_bp,
    ]:
        app.register_blueprint(bp)

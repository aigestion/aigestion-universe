from .digital_twin import twin_bp
from .gesture_recognition import gesture_bp
from .haptic_language import haptic_bp
from .life_score import life_score_bp
from .light_painting import light_painting_bp
from .physical_anchor import anchor_bp
from .proximity_awareness import proximity_bp
from .spatial_audio import spatial_bp
from .temperature_feedback import temp_bp
from .voice_cloning import voice_clone_bp


def register_embodiment(app):
    for bp in [
        haptic_bp,
        spatial_bp,
        light_painting_bp,
        temp_bp,
        gesture_bp,
        proximity_bp,
        voice_clone_bp,
        twin_bp,
        anchor_bp,
        life_score_bp,
    ]:
        app.register_blueprint(bp)

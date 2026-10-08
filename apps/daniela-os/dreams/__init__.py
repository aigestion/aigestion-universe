from .astral_radio import radio_bp
from .dream_journal import journal_bp
from .dream_symbols import symbols_bp
from .lucid_triggers import lucid_bp
from .nap_optimizer import nap_bp
from .nightmare_soother import soother_bp
from .sleep_cycle import cycle_bp
from .sleep_score import score_bp
from .sleep_stories import stories_bp
from .white_noise import noise_bp


def register_dreams(app):
    for bp in [
        stories_bp,
        journal_bp,
        lucid_bp,
        noise_bp,
        cycle_bp,
        soother_bp,
        nap_bp,
        symbols_bp,
        score_bp,
        radio_bp,
    ]:
        app.register_blueprint(bp)

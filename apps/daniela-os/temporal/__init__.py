from .anniversary_tracker import anni_bp
from .birthday_engine import bday_bp
from .countdown_engine import cd_bp
from .deja_vu_log import deja_bp
from .future_letters import letters_bp
from .milestone_map import map_bp
from .moment_freezer import freeze_bp
from .season_mood import season_bp
from .time_capsule import cap_bp
from .year_progress import year_bp


def register_temporal(app):
    for bp in [
        anni_bp,
        cd_bp,
        cap_bp,
        letters_bp,
        season_bp,
        map_bp,
        deja_bp,
        bday_bp,
        year_bp,
        freeze_bp,
    ]:
        app.register_blueprint(bp)

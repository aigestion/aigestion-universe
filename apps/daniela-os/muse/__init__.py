from .brainstorm_storm import storm_bp
from .character_lab import charlab_bp
from .dialogue_doctor import dialog_bp
from .idea_garden import garden_bp
from .muse_roulette import roulette_bp
from .plot_twister import twist_bp
from .poetry_forge import poetry_bp
from .song_sketch import song_bp
from .story_cowriter import cow_bp
from .world_builder import world_bp


def register_muse(app):
    for bp in [
        cow_bp,
        poetry_bp,
        storm_bp,
        garden_bp,
        twist_bp,
        charlab_bp,
        world_bp,
        dialog_bp,
        song_bp,
        roulette_bp,
    ]:
        app.register_blueprint(bp)

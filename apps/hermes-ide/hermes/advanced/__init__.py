

from .eval_system import eval_system_bp
from .multi_provider import multi_provider_bp
from .plugin_marketplace import plugin_marketplace_bp
from .self_improvement import self_improvement_bp
from .skill_creator import skill_creator_bp


def register_advanced(app):
    for bp in [multi_provider_bp, skill_creator_bp, plugin_marketplace_bp, eval_system_bp, self_improvement_bp]:
        app.register_blueprint(bp)



from .counterfactual_memory import counterfactual_bp
from .emotional_memory import emotional_mem_bp
from .episodic_memory import episodic_bp
from .memory_consolidation import consolidation_bp
from .memory_search import mem_search_bp
from .procedural_memory import procedural_bp
from .semantic_memory import semantic_bp
from .social_memory import social_bp
from .spatial_memory import spatial_bp
from .temporal_memory import temporal_bp


def register_memory(app):
    for bp in [episodic_bp, semantic_bp, procedural_bp, emotional_mem_bp, spatial_bp, social_bp, temporal_bp, counterfactual_bp, consolidation_bp, mem_search_bp]:
        app.register_blueprint(bp)

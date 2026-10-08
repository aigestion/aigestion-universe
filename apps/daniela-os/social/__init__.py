from .apology_helper import apol_bp
from .birthday_radar import radar_bp
from .celebration_planner import party_bp
from .compliment_generator import compl_bp
from .contact_insights import contacts_bp
from .family_hub import family_bp
from .gift_oracle import gift_bp
from .gratitude_exchange import grat_bp
from .love_languages import love_bp
from .reunion_optimizer import reunion_bp


def register_social(app):
    for bp in [
        gift_bp,
        radar_bp,
        contacts_bp,
        family_bp,
        grat_bp,
        compl_bp,
        apol_bp,
        party_bp,
        reunion_bp,
        love_bp,
    ]:
        app.register_blueprint(bp)

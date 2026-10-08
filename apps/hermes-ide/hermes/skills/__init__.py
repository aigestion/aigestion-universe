

from .code_review import code_review_bp
from .creative_writer import creative_bp
from .data_analyst import data_analyst_bp
from .email_intelligence import email_bp
from .finance_tracker import finance_bp
from .health_monitor import health_bp
from .language_tutor import language_bp
from .meeting_prep import meeting_prep_bp
from .research_assistant import research_bp
from .smart_home_hub import smart_home_bp


def register_skills(app):
    for bp in [code_review_bp, email_bp, meeting_prep_bp, research_bp, creative_bp, data_analyst_bp, smart_home_bp, finance_bp, health_bp, language_bp]:
        app.register_blueprint(bp)

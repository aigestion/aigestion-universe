

from .auto_reporter import reporter_bp
from .backup_scheduler import backup_bp
from .code_auto_reviewer import code_review_auto_bp
from .email_auto_responder import auto_responder_bp
from .evening_summary import evening_bp
from .file_organizer import file_organizer_bp
from .meeting_note_taker import note_taker_bp
from .morning_briefing import morning_bp
from .smart_reminders import reminders_bp
from .weekly_review import weekly_bp


def register_automation(app):
    for bp in [morning_bp, evening_bp, weekly_bp, reporter_bp, reminders_bp, auto_responder_bp, code_review_auto_bp, note_taker_bp, file_organizer_bp, backup_bp]:
        app.register_blueprint(bp)

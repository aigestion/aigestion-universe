from .calm_anchor import anchor_bp
from .checkin_engine import checkin_bp
from .digital_will import will_bp
from .guardian_summary import summary_bp
from .home_safe import home_bp
from .med_reminder import meds_bp
from .night_watch import watch_bp
from .safe_contacts import safe_bp
from .scam_shield import scam_bp
from .sos_beacon import sos_bp


def register_guardian(app):
    for bp in [
        checkin_bp,
        sos_bp,
        meds_bp,
        home_bp,
        will_bp,
        scam_bp,
        safe_bp,
        watch_bp,
        anchor_bp,
        summary_bp,
    ]:
        app.register_blueprint(bp)

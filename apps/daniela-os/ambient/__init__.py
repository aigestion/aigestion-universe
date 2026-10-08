from .ambient_sounds import sounds_bp
from .aura_projection import aura_bp
from .breathing_light import breathing_bp
from .desktop_pet import pet_bp
from .dual_presence import dual_bp
from .ghost_mode import ghost_bp
from .heartbeat import heartbeat_bp
from .notification_breathing import noti_breath_bp
from .presence_sensor import presence_bp
from .room_tone import room_bp


def register_ambient(app):
    for bp in [
        heartbeat_bp,
        breathing_bp,
        sounds_bp,
        pet_bp,
        presence_bp,
        aura_bp,
        ghost_bp,
        noti_breath_bp,
        room_bp,
        dual_bp,
    ]:
        app.register_blueprint(bp)

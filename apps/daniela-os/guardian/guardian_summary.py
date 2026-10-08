import time

from flask import Blueprint, jsonify

try:
    from .checkin_engine import _state as _checkins
except ImportError:
    _checkins = {"schedules": []}
try:
    from .med_reminder import _state as _meds
except ImportError:
    _meds = {"meds": [], "taken": []}
try:
    from .home_safe import _state as _trips
except ImportError:
    _trips = {"trips": []}
try:
    from .sos_beacon import _state as _sos
except ImportError:
    _sos = {"active": None}

summary_bp = Blueprint("guardian_summary", __name__)


@summary_bp.route("/api/guardian/summary/today")
def gs_today():
    now = time.time()
    late = [
        s["who"]
        for s in _checkins.get("schedules", [])
        if (now - s.get("last_ok", now)) > s.get("every_min", 120) * 60
    ]
    open_trips = [t["id"] for t in _trips.get("trips", []) if not t.get("arrived")]
    return jsonify(
        {
            "checkins_total": len(_checkins.get("schedules", [])),
            "checkins_late": late,
            "meds_tracked": len(_meds.get("meds", [])),
            "doses_today": len(_meds.get("taken", [])),
            "open_trips": open_trips,
            "sos_active": _sos.get("active") is not None,
            "verdict": "Todo en calma."
            if not late and not open_trips and not _sos.get("active")
            else "Hay asuntos pendientes arriba.",
        }
    )


@summary_bp.route("/api/guardian/summary/alerts")
def gs_alerts():
    alerts = []
    if _sos.get("active"):
        alerts.append("SOS ACTIVO")
    now = time.time()
    for t in _trips.get("trips", []):
        if not t.get("arrived") and now > t.get("expires_at", now):
            alerts.append(f"Viaje {t['id']} vencido sin llegada")
    return jsonify({"alerts": alerts})

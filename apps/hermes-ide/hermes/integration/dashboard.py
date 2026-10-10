from flask import Blueprint, jsonify

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/api/hermes/dashboard/status")
def dashboard_status():
    return jsonify({
        "hermes": {"port": 9300, "modules": 50, "status": "active"},
        "daniela": {"port": 9200, "modules": 53, "status": "active"},
        "epic_pc": {"port": 5020, "modules": 62, "status": "active"},
        "total": 165
    })

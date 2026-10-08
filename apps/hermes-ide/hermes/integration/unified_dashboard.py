from flask import Blueprint, jsonify

unified_dash_bp = Blueprint("unified_dashboard", __name__)

@unified_dash_bp.route("/api/hermes/unified/status")
def ud_status():
    return jsonify({
        "hermes": {"port": 9300, "modules": 50, "status": "active"},
        "daniela": {"port": 9200, "modules": 53, "status": "active"},
        "epic_pc": {"port": 5020, "modules": 62, "status": "active"},
        "total": 165
    })

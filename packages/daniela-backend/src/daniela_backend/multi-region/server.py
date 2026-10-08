"""
aig Multi-Region Control Server
=======================================
Flask API on port 9911: region status, weights, drills, failover.

Endpoints:
  GET  /health
  GET  /api/regions/status    matrix + weights (+ quorum, failover)
  GET  /api/regions/weights
  GET  /api/regions/quorum
  POST /api/regions/drill     simulation by default
  POST /api/regions/failover  requires confirm token

Autor: aig Team
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request

try:
    from .config import REGIONS, get_all_regions
except ImportError:
    from config import REGIONS, get_all_regions

try:
    from .failover import FailoverManager, RegionStatus
except ImportError:
    from failover import FailoverManager, RegionStatus

try:
    from .health_mesh import HealthMesh
except ImportError:
    from health_mesh import HealthMesh

try:
    from .dns_sim import DnsWeightTable
except ImportError:
    from dns_sim import DnsWeightTable

try:
    from .failover_drill import FailoverDrill
except ImportError:
    from failover_drill import FailoverDrill


PORT = 9911
CONFIRM_TOKEN = os.environ.get("REGIONS_CONFIRM_TOKEN", "aig-confirm-9911")

_default_mesh = HealthMesh()
_default_dns = DnsWeightTable()
_default_manager = FailoverManager(
    local_region=os.environ.get("REGION", "eu-west")
)


def create_app(
    mesh: HealthMesh | None = None,
    dns: DnsWeightTable | None = None,
    manager: FailoverManager | None = None,
) -> Flask:
    """Flask app factory (injectable deps for tests)."""
    _mesh = mesh if mesh is not None else _default_mesh
    _dns = dns if dns is not None else _default_dns
    _manager = manager if manager is not None else _default_manager

    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "regions"})

    @app.get("/api/regions/status")
    def regions_status():
        return jsonify(
            {
                "matrix": _mesh.get_matrix(),
                "weights": _dns.get_table(),
                "quorum": _mesh.quorum_check(),
                "failover": _manager.get_status(),
            }
        )

    @app.get("/api/regions/weights")
    def regions_weights():
        return jsonify({"weights": _dns.get_table()})

    @app.get("/api/regions/quorum")
    def regions_quorum():
        return jsonify(_mesh.quorum_check())

    @app.post("/api/regions/drill")
    def regions_drill():
        body = request.get_json(silent=True) or {}
        victim = body.get("victim") or get_all_regions()[0].name
        real_drain = bool(body.get("real_drain", False))
        if victim not in REGIONS:
            return jsonify({"error": f"Unknown region: {victim}"}), 400
        if real_drain and body.get("confirm") != CONFIRM_TOKEN:
            return (
                jsonify({"error": "confirm token required for real drain"}),
                403,
            )
        report = FailoverDrill(manager=_manager, dns=_dns).run(
            victim, real_drain=real_drain
        )
        return jsonify({"report": report})

    @app.post("/api/regions/failover")
    def regions_failover():
        body = request.get_json(silent=True) or {}
        region = body.get("region")
        if body.get("confirm") != CONFIRM_TOKEN:
            return jsonify({"error": "confirm token required"}), 403
        if region not in REGIONS:
            return jsonify({"error": f"Unknown region: {region}"}), 400
        _manager._region_status[region] = RegionStatus.DOWN
        event = _manager.trigger_failover(region)
        if event is None:
            return jsonify({"error": f"No healthy target for {region}"}), 503
        weights = _dns.shift_weight(region, event.target_region)
        return jsonify(
            {
                "event": {
                    "source_region": event.source_region,
                    "target_region": event.target_region,
                    "reason": event.reason,
                    "timestamp": event.timestamp,
                },
                "weights": weights,
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    _default_mesh.start()
    try:
        app.run(host="0.0.0.0", port=PORT)
    finally:
        _default_mesh.stop()

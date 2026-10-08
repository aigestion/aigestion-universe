"""Flask API for chaos_engine (canonical skeleton: PORT from env, /health)."""

from __future__ import annotations

import os
from typing import Any

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore

from .experiments import BlastRadius, Experiment
from .faults import create_fault
from .scheduler import ChaosScheduler

PORT = int(os.getenv("SERVICE_PORT", "9910"))
VERSION = "1.0.0"


def create_app(scheduler: ChaosScheduler | None = None) -> Flask:
    if Flask is None:
        raise RuntimeError("Flask is not installed. Run: pip install flask")
    app = Flask(__name__)
    app.config["SCHEDULER"] = scheduler or ChaosScheduler()
    app.config["HISTORY"] = []
    app.config["RUNNING"] = False

    def _sched() -> ChaosScheduler:
        return app.config["SCHEDULER"]

    @app.get("/api/chaos/status")
    def status() -> Any:
        sched = _sched()
        return jsonify(
            {
                "service": "chaos_engine",
                "status": "ok",
                "version": VERSION,
                "armed": sched.is_armed,
                "kill_switch_engaged": sched.kill_switch_engaged,
                "running": bool(app.config["RUNNING"]),
                "history_count": len(app.config["HISTORY"]),
                "port": PORT,
            }
        )

    @app.get("/health")
    def health() -> Any:
        return jsonify({"status": "ok", "service": "chaos_engine"})

    @app.get("/api/chaos/safety")
    def safety() -> Any:
        return jsonify(_sched().safety_status())

    @app.get("/api/chaos/history")
    def history() -> Any:
        hist: list[dict[str, Any]] = app.config["HISTORY"]
        return jsonify({"history": hist, "count": len(hist)})

    @app.post("/api/chaos/experiment")
    def run_experiment() -> Any:
        sched = _sched()
        payload: dict[str, Any] = request.get_json(silent=True) or {}
        dry_run = bool(payload.get("dry_run", True))
        name = str(payload.get("name", "ad-hoc-experiment"))
        fault_specs = payload.get("faults", [{"type": "latency_injection", "target": "demo", "duration": 5}])

        faults = []
        try:
            for spec in fault_specs:
                if isinstance(spec, dict):
                    faults.append(
                        create_fault(
                            spec.get("type", "latency_injection"),
                            target=spec.get("target", "default"),
                            duration=float(spec.get("duration", 5)),
                            **{k: v for k, v in spec.items() if k not in ("type", "target", "duration")},
                        )
                    )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        if not dry_run:
            # Live runs require full safety: armed, in-window, kill-switch off.
            if not sched.can_run():
                return jsonify({"error": "live run blocked by safety gate", "safety": sched.safety_status()}), 403

        app.config["RUNNING"] = True
        try:
            exp = Experiment(
                name=name,
                faults=faults,
                blast_radius=BlastRadius(environment=payload.get("environment", "staging")),
                dry_run=dry_run,
            )
            result = exp.run()
        finally:
            app.config["RUNNING"] = False
        app.config["HISTORY"].append(result.to_dict())
        code = 200 if result.success else 500
        return jsonify(result.to_dict()), code

    @app.post("/api/chaos/stop")
    def stop() -> Any:
        sched = _sched()
        sched.engage_kill_switch()
        app.config["RUNNING"] = False
        return jsonify({"stopped": True, "kill_switch_engaged": True, "safety": sched.safety_status()})

    return app


def main() -> None:
    app = create_app()
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()

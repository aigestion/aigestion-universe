#!/usr/bin/env python3
"""
PA-15: Pixel as Second Screen - dashboard en el movil
=========================================================
El Pixel funciona como segunda pantalla del PC.
Muestra el dashboard de Daniela (health score, agent status,
activity feed, metrics). Touch controls para interactuar.

El navegador del Pixel apunta a:
  http://<PC_IP>:5050/pixel-dashboard

Rutas en daniela_os.py:
  - GET /pixel-dashboard         (dashboard HTML para movil)
  - GET /api/pixel/dashboard/data (datos del dashboard en JSON)

Coste: $0/mes
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass

# ── Config ───────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "second_screen")
STATE_FILE = os.path.join(STATE_DIR, "second_screen_state.json")
TEMPLATE_FILE = os.path.join(PROJECT_ROOT, "templates", "pixel_dashboard.html")


# ── Data classes ─────────────────────────────────────────────


@dataclass
class DashboardData:
    health_score: int = 0
    agent_count: int = 0
    active_agents: int = 0
    open_findings: int = 0
    pixel_online: bool = False
    battery_pct: int = 0
    last_update: float = 0.0
    activity: list[dict] = None  # type: ignore

    def __post_init__(self):
        if self.activity is None:
            self.activity = []


# ── Pixel Second Screen ──────────────────────────────────────


class PixelSecondScreen:
    """Dashboard data aggregator for the Pixel second screen."""

    def __init__(self):
        self._last_data = DashboardData()

    def get_dashboard_data(self) -> dict:
        """Aggregate data from all modules for the dashboard."""
        data = DashboardData(last_update=time.time())

        # Health score + findings from SIL
        try:
            from sil_engine import SelfImprovementLoop
            sil = SelfImprovementLoop()
            state = sil.get_state() if hasattr(sil, "get_state") else {}
            data.health_score = state.get("health_score", 0)
            findings = state.get("findings", [])
            data.open_findings = len([f for f in findings if not f.get("resolved", False)])
        except Exception:
            pass

        # Agents
        try:
            import agents as agents_mod
            agent_list = getattr(agents_mod, "AGENTS", {})
            data.agent_count = len(agent_list)
            data.active_agents = len([
                a for a in agent_list.values()
                if str(getattr(a, "status", "")).lower() == "active"
            ])
        except Exception:
            pass

        # Pixel status
        try:
            from pixel_bridge_hub import PixelBridgeHub
            hub = PixelBridgeHub()
            status = hub.get_status()
            data.pixel_online = status.get("online", False)
            if data.pixel_online:
                bat = hub.get_battery()
                if bat:
                    data.battery_pct = bat.get("percentage", 0)
        except Exception:
            pass

        # Activity feed (recent sensor or notification events)
        try:
            from fcm_real_bridge import get_instance as get_bridge
            bridge = get_bridge()
            recent = bridge.get_recent_outbound(limit=8)
            data.activity = [
                {"time": r.get("timestamp", 0), "text": f"{r.get('title', '')}: {r.get('body', '')[:60]}"}
                for r in recent
            ]
        except Exception:
            pass

        self._last_data = data
        return asdict(data)

    def render_dashboard(self) -> str:
        """Render the mobile dashboard HTML."""
        if os.path.exists(TEMPLATE_FILE):
            with open(TEMPLATE_FILE, encoding="utf-8") as f:
                return f.read()
        return "<h1>Dashboard template not found</h1>"

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self._last_data), f, indent=2, ensure_ascii=False, default=str)


# ── Singleton ─────────────────────────────────────────────────

_instance: PixelSecondScreen | None = None


def get_instance() -> PixelSecondScreen:
    global _instance
    if _instance is None:
        _instance = PixelSecondScreen()
    return _instance


# ── Flask route registration ──────────────────────────────────


def register_second_screen_routes(flask_app):
    """Register second screen routes in daniela_os.py."""

    @flask_app.route("/pixel-dashboard")
    def pixel_dashboard():
        """Mobile dashboard HTML for the Pixel second screen."""
        return flask_app.send_static_file if False else get_instance().render_dashboard()

    @flask_app.route("/api/pixel/dashboard/data")
    def pixel_dashboard_data():
        """Dashboard data as JSON (for auto-refresh)."""
        return flask_app.jsonify(get_instance().get_dashboard_data())

    print("[Second Screen] Routes registered: /pixel-dashboard, /api/pixel/dashboard/data")


# ── CLI ───────────────────────────────────────────────────────

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pixel_second_screen.py [data|render]")
        return

    cmd = sys.argv[1]
    screen = get_instance()

    if cmd == "data":
        print(json.dumps(screen.get_dashboard_data(), indent=2, default=str))
    elif cmd == "render":
        html = screen.render_dashboard()
        print(f"Dashboard HTML: {len(html)} chars")
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()

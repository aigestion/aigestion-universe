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
from typing import Dict, List, Optional

# ── Config ───────────────────────────────────────────────────

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    activity: List[Dict] = None  # type: ignore

    def __post_init__(self):
        if self.activity is None:
            self.activity = []


# ── Pixel Second Screen ──────────────────────────────────────


class PixelSecondScreen:
    """Dashboard data aggregator for the Pixel second screen."""

    def __init__(self):
        self._last_data = DashboardData()

    def get_dashboard_data(self) -> Dict:
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
            data.active_agents = len(
                [
                    a
                    for a in agent_list.values()
                    if str(getattr(a, "status", "")).lower() == "active"
                ]
            )
        except Exception:
            pass

        # Pixel status
        try:
            from bridges.pixel.pixel_bridge_hub import PixelBridgeHub

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
            from bridges.comms.fcm_real_bridge import get_instance as get_bridge

            bridge = get_bridge()
            recent = bridge.get_recent_outbound(limit=8)
            data.activity = [
                {
                    "time": r.get("timestamp", 0),
                    "text": f"{r.get('title', '')}: {r.get('body', '')[:60]}",
                }
                for r in recent
            ]
        except Exception:
            pass

        self._last_data = data
        return asdict(data)

    def render_dashboard(self) -> str:
        """Render the mobile dashboard HTML."""
        if os.path.exists(TEMPLATE_FILE):
            with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>Dashboard template not found</h1>"

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self._last_data), f, indent=2, ensure_ascii=False, default=str)


# ── Singleton ─────────────────────────────────────────────────

_instance: Optional[PixelSecondScreen] = None


def get_instance() -> PixelSecondScreen:
    global _instance
    if _instance is None:
        _instance = PixelSecondScreen()
    return _instance


# ── HUD Command (Fase 3, idea #11) ─────────────────────────────
# Cola unificada pendiente de tap humano: grises del court,
# veredictos revisar/bloquear de invoice, tareas edge muertas.
# Cada accion ejecuta operacion real (decidir / visto / reencolar).


def hud_pendientes() -> List[Dict]:
    """Agrega pendientes de court + invoice + edge. Nunca lanza."""
    items: List[Dict] = []
    try:
        from agents.automation.agent_court import cola_pendiente

        for c in cola_pendiente():
            items.append(
                {
                    "id": c.get("id", ""),
                    "origen": "court",
                    "titulo": str(c.get("subject", ""))[:80] or c.get("id", ""),
                    "detalle": f"{c.get('categoria', '?')} (conf {c.get('confianza', '?')})",
                    "acciones": ["aprobar", "rechazar"],
                }
            )
    except Exception:
        pass
    try:
        from agents.documents.agent_invoice_graph import _leer_ledger

        todos = _leer_ledger(solo_facturas=False)
        vistos = set()
        for e in todos:
            if e.get("ev") == "revision":
                vistos.add((str(e.get("proveedor", "")).lower(), str(e.get("numero", ""))))
        for e in todos:
            if e.get("ev") != "veredicto" or e.get("veredicto") == "pagar":
                continue
            clave = (str(e.get("proveedor", "")).lower(), str(e.get("numero", "")))
            if clave in vistos:
                continue
            items.append(
                {
                    "id": f"{e.get('proveedor', '')}|{e.get('numero', '')}",
                    "origen": "invoice",
                    "titulo": f"{e.get('veredicto', '').upper()}: {e.get('proveedor', '')} "
                    f"{e.get('numero', '')} ({e.get('total', '?')} EUR)",
                    "detalle": "; ".join(e.get("motivos", [])[:2]),
                    "acciones": ["visto"],
                }
            )
    except Exception:
        pass
    try:
        from services.mesh.edge_node import _plegar

        for t in _plegar().values():
            if t.get("estado") == "dead":
                items.append(
                    {
                        "id": t["id"],
                        "origen": "edge",
                        "titulo": f"Tarea muerta: {t.get('tipo', '?')}",
                        "detalle": f"nodo {t.get('nodo') or '?'} · {t.get('intentos', 0)} intentos",
                        "acciones": ["reencolar"],
                    }
                )
    except Exception:
        pass
    return items


def hud_accion(origen: str, id: str, accion: str, extra: Optional[Dict] = None) -> Dict:
    """Ejecuta el tap. Devuelve ok/False honesto. Nunca lanza."""
    try:
        if origen == "court" and accion in ("aprobar", "rechazar"):
            from agents.automation.agent_court import decidir

            return decidir(id, accion, (extra or {}).get("motivo", "desde HUD"))
        if origen == "invoice" and accion == "visto":
            from agents.documents.agent_invoice_graph import _anexar

            prov, _, num = id.partition("|")
            _anexar(
                {
                    "ev": "revision",
                    "proveedor": prov,
                    "numero": num,
                    "por": "HUD",
                    "accion": "visto",
                }
            )
            return {"ok": True, "id": id}
        if origen == "edge" and accion == "reencolar":
            from services.mesh.edge_node import _plegar, dispatch_task

            t = _plegar().get(id)
            if not t:
                return {"ok": False, "error": "tarea desconocida"}
            return dispatch_task(
                t.get("tipo", ""), t.get("payload") or {}, int(t.get("prioridad", 2))
            )
        return {"ok": False, "error": f"accion no soportada: {origen}/{accion}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ── Flask route registration ──────────────────────────────────


def register_second_screen_routes(flask_app):
    """Register second screen routes in daniela_os.py."""
    # jsonify es del modulo flask, no del objeto app (usar app.jsonify
    # revienta en 500: bug preexistente que esta edicion corrige).
    from flask import jsonify as _jsonify

    @flask_app.route("/pixel-dashboard")
    def pixel_dashboard():
        """Mobile dashboard HTML for the Pixel second screen."""
        return flask_app.send_static_file if False else get_instance().render_dashboard()

    @flask_app.route("/api/pixel/dashboard/data")
    def pixel_dashboard_data():
        """Dashboard data as JSON (for auto-refresh)."""
        return _jsonify(get_instance().get_dashboard_data())

    @flask_app.route("/api/pixel/hud/pendientes")
    def hud_pendientes_route():
        """Cola unificada pendiente de tap humano."""
        return _jsonify({"ok": True, "pendientes": hud_pendientes()})

    @flask_app.route("/api/pixel/hud/accion", methods=["POST"])
    def hud_accion_route():
        """Ejecuta un tap: {origen, id, accion}."""
        from flask import request as freq

        data = freq.get_json(force=True, silent=True) or {}
        r = hud_accion(
            str(data.get("origen", "")),
            str(data.get("id", "")),
            str(data.get("accion", "")),
            data.get("extra") or {},
        )
        return _jsonify(r), (200 if r.get("ok") else 400)

    print(
        "[Second Screen] Routes registered: /pixel-dashboard, /api/pixel/dashboard/data, /api/pixel/hud/*"
    )


# ── CLI ───────────────────────────────────────────────────────


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pixel_second_screen.py [data|render|pendientes]")
        return

    cmd = sys.argv[1]
    screen = get_instance()

    if cmd == "data":
        print(json.dumps(screen.get_dashboard_data(), indent=2, default=str))
    elif cmd == "render":
        html = screen.render_dashboard()
        print(f"Dashboard HTML: {len(html)} chars")
    elif cmd == "pendientes":
        for p in hud_pendientes():
            print(f"  [{p['origen']}] {p['titulo'][:70]} -> {','.join(p['acciones'])}")
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
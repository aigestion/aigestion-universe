#!/usr/bin/env python3
"""Pixel Edge Node (Fase 3, idea #2) — el telefono como worker del swarm.

El Pixel deja de ser espejo y pasa a ejecutar tareas: OCR facturas, voz,
geofence, camara. Este modulo es el LADO SERVIDOR (corre en el PC):

- Cola por log de eventos (`data/edge/edge_log.jsonl`): created/claimed/
  done. Sin migraciones, legible, tolerante a caidas.
- Lease con TTL: si un worker muere, la tarea vuelve a pending.
- Politica bateria (via `battery_aware_scheduler`): full→todo,
  normal→sin tareas pesadas, save→solo urgentes. Cargando = full.
- Redis OPCIONAL como canal de aviso (no como store): si hay
  REDIS_URL y responde, publica; si no, local con flag honesto.
- El worker vive en `edge_worker.py` (raiz, se sincroniza al telefono).

Protocolo (rutas al final): POST /api/edge/dispatch,
GET /api/edge/tasks/next, POST /api/edge/tasks/<id>/result,
GET /api/edge/status.

CLI: python edge_node.py dispatch <tipo> '<json>' | next <nodo> | status
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from flask import jsonify, request
except ImportError:  # pragma: no cover
    jsonify = None  # type: ignore
    request = None  # type: ignore

from services.sensors.battery_aware_scheduler import battery_scheduler

from paths import DATA_DIR

EDGE_LOG = DATA_DIR / "edge" / "edge_log.jsonl"

# tipo -> coste energetico. Pesadas solo en modo full.
COSTE_TAREA = {
    "ocr_factura": "high",
    "transcribir_voz": "high",
    "foto_camara": "medium",
    "chequeo_geofence": "low",
    "estado_nodo": "low",
}

# modo bateria -> costes permitidos (save solo deja pasar urgentes).
COSTES_POR_MODO = {
    "full": {"high", "medium", "low"},
    "normal": {"medium", "low"},
    "save": {"low"},
}

LEASE_TTL_S = 300
LEASE_TTL_PESADAS_S = 900
MAX_INTENTOS = 3


def _ahora_iso() -> str:
    return datetime.now().isoformat()


def _nueva_id() -> str:
    return f"edge-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"


def _anexar(evento: Dict[str, Any]) -> None:
    try:
        EDGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        evento = dict(evento)
        evento.setdefault("ts", _ahora_iso())
        with open(EDGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _leer_eventos(max_lines: int = 2000) -> List[Dict[str, Any]]:
    if not EDGE_LOG.exists():
        return []
    try:
        lines = EDGE_LOG.read_text(encoding="utf-8").splitlines()[-max_lines:]
    except OSError:
        return []
    eventos = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            eventos.append(json.loads(line))
        except ValueError:
            continue
    return eventos


def _plegar() -> Dict[str, Dict[str, Any]]:
    """Reconstruye el estado plegando eventos. Tareas vencidas vuelven
    a pending; con >=MAX_INTENTOS fallos quedan dead."""
    tareas: Dict[str, Dict[str, Any]] = {}
    for ev in _leer_eventos():
        tipo = ev.get("ev")
        tid = ev.get("task_id", "")
        if not tid:
            continue
        if tipo == "created":
            tareas[tid] = {
                "id": tid,
                "tipo": ev.get("tipo", ""),
                "payload": ev.get("payload", {}),
                "prioridad": int(ev.get("prioridad", 2)),
                "estado": "pending",
                "intentos": 0,
                "nodo": None,
                "lease_hasta": 0.0,
                "creada_ts": ev.get("ts", ""),
                "resultado": None,
                "error": "",
            }
        elif tipo == "claimed" and tid in tareas:
            t = tareas[tid]
            t["estado"] = "claimed"
            t["nodo"] = ev.get("nodo")
            t["lease_hasta"] = float(ev.get("lease_hasta", 0.0))
            t["intentos"] = t.get("intentos", 0) + 1
        elif tipo == "done" and tid in tareas:
            t = tareas[tid]
            t["estado"] = "done"
            t["resultado"] = ev.get("resultado")
            t["nodo"] = ev.get("nodo", t.get("nodo"))
        elif tipo == "failed" and tid in tareas:
            t = tareas[tid]
            t["error"] = str(ev.get("error", ""))[:300]
            t["estado"] = "pending" if t.get("intentos", 0) < MAX_INTENTOS else "dead"
            t["nodo"] = None
            t["lease_hasta"] = 0.0
    ahora = time.time()
    for t in tareas.values():
        if t["estado"] == "claimed" and t["lease_hasta"] < ahora:
            if t.get("intentos", 0) >= MAX_INTENTOS:
                t["estado"] = "dead"
            else:
                t["estado"] = "pending"
                t["nodo"] = None
    return tareas


def _redis_aviso(canal: str, mensaje: str) -> str:
    """Publica aviso best-effort. Devuelve up/down/no_configurado."""
    url = (os.getenv("REDIS_URL") or "").strip()
    if not url:
        return "no_configurado"
    try:
        import redis  # type: ignore

        r = redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
        r.publish(canal, mensaje)
        return "up"
    except Exception:
        return "down"


# ── API del nodo ─────────────────────────────────────────────────


def dispatch_task(
    tipo: str, payload: Optional[Dict[str, Any]] = None, prioridad: int = 2
) -> Dict[str, Any]:
    """Encola una tarea edge. Devuelve {"ok", "task_id"} o error."""
    if tipo not in COSTE_TAREA:
        return {
            "ok": False,
            "error": f"tipo desconocido: {tipo} " f"(validos: {sorted(COSTE_TAREA)})",
        }
    tid = _nueva_id()
    _anexar(
        {
            "ev": "created",
            "task_id": tid,
            "tipo": tipo,
            "payload": payload or {},
            "prioridad": prioridad,
        }
    )
    redis = _redis_aviso("edge:tareas", tid)
    return {"ok": True, "task_id": tid, "tipo": tipo, "redis": redis}


def politica_para(bateria_pct: Optional[int], cargando: bool = False) -> Dict[str, Any]:
    """Modo bateria + costes permitidos para un worker."""
    if bateria_pct is None:
        modo = "normal"  # sin dato: conservador
    else:
        try:
            modo = battery_scheduler.determine_mode(int(bateria_pct), bool(cargando))
        except Exception:
            modo = "normal"
    if cargando:
        modo = "full"
    if modo not in COSTES_POR_MODO:
        modo = "normal"
    return {"modo": modo, "costes": sorted(COSTES_POR_MODO[modo])}


def next_task(
    node_id: str, bateria_pct: Optional[int] = None, cargando: bool = False
) -> Dict[str, Any]:
    """Reclama la siguiente tarea permitida por bateria (con lease).

    Devuelve la tarea o {"hold": motivo} si no hay nada apto ahora.
    """
    if not (node_id or "").strip():
        return {"hold": "node_id requerido"}
    tareas = _plegar()
    pendientes = [t for t in tareas.values() if t["estado"] == "pending"]
    if not pendientes:
        return {"hold": "cola vacia"}
    pol = politica_para(bateria_pct, cargando)
    aptas = [
        t
        for t in pendientes
        if COSTE_TAREA.get(t["tipo"]) in pol["costes"]
        and (pol["modo"] != "save" or t["prioridad"] == 0)
    ]
    if not aptas:
        pesadas = sum(1 for t in pendientes if COSTE_TAREA.get(t["tipo"]) == "high")
        return {"hold": f"bateria en modo {pol['modo']}: {pesadas} pesadas en espera"}
    aptas.sort(key=lambda t: (t["prioridad"], t["creada_ts"]))
    elegida = aptas[0]
    ttl = LEASE_TTL_PESADAS_S if COSTE_TAREA.get(elegida["tipo"]) == "high" else LEASE_TTL_S
    _anexar(
        {
            "ev": "claimed",
            "task_id": elegida["id"],
            "nodo": node_id,
            "lease_hasta": time.time() + ttl,
        }
    )
    return {
        "ok": True,
        "task_id": elegida["id"],
        "tipo": elegida["tipo"],
        "payload": elegida["payload"],
        "lease_s": ttl,
        "modo_bateria": pol["modo"],
    }


def submit_result(task_id: str, node_id: str, resultado: Any) -> Dict[str, Any]:
    """Registra el resultado de un worker. Devuelve ok/False honesto."""
    tareas = _plegar()
    t = tareas.get(task_id)
    if t is None:
        return {"ok": False, "error": "task_id desconocido"}
    if t["estado"] == "done":
        return {"ok": False, "error": "tarea ya cerrada"}
    _anexar({"ev": "done", "task_id": task_id, "nodo": node_id, "resultado": resultado})
    _redis_aviso("edge:resultados", task_id)
    return {"ok": True, "task_id": task_id}


def fail_task(task_id: str, node_id: str, error: str) -> Dict[str, Any]:
    """Marca un intento como fallido (reintenta o muere por contador)."""
    tareas = _plegar()
    if task_id not in tareas:
        return {"ok": False, "error": "task_id desconocido"}
    _anexar({"ev": "failed", "task_id": task_id, "nodo": node_id, "error": error})
    return {"ok": True, "task_id": task_id}


def estado() -> Dict[str, Any]:
    """Foto de la cola: conteos, nodos vistos, backend, politica."""
    tareas = list(_plegar().values())
    por_estado: Dict[str, int] = {}
    por_tipo: Dict[str, int] = {}
    nodos: Dict[str, Any] = {}
    for t in tareas:
        por_estado[t["estado"]] = por_estado.get(t["estado"], 0) + 1
        if t["estado"] == "pending":
            por_tipo[t["tipo"]] = por_tipo.get(t["tipo"], 0) + 1
        if t.get("nodo"):
            nodos[t["nodo"]] = nodos.get(t["nodo"], 0) + 1
    return {
        "ok": True,
        "tareas_total": len(tareas),
        "por_estado": por_estado,
        "pending_por_tipo": por_tipo,
        "nodos": nodos,
        "redis": _redis_aviso("edge:ping", "ping"),
        "politica": {"full": "todo", "normal": "sin pesadas", "save": "solo urgentes"},
        "tipos": sorted(COSTE_TAREA),
    }


# ── Rutas Flask ──────────────────────────────────────────────────


def register_edge_routes(app) -> None:
    """Protocolo worker: dispatch / next / result / status."""

    @app.route("/api/edge/dispatch", methods=["POST"])
    def edge_dispatch():
        data = request.get_json(force=True, silent=True) or {}
        r = dispatch_task(
            str(data.get("tipo", "")), data.get("payload") or {}, int(data.get("prioridad", 2))
        )
        return jsonify(r), (200 if r.get("ok") else 400)

    @app.route("/api/edge/tasks/next")
    def edge_next():
        node_id = request.args.get("node_id", "")
        bat = request.args.get("bateria", "")
        try:
            bateria = int(bat) if bat != "" else None
        except ValueError:
            bateria = None
        cargando = str(request.args.get("cargando", "")).lower() in ("1", "true", "si")
        return jsonify(next_task(node_id, bateria, cargando))

    @app.route("/api/edge/tasks/<task_id>/result", methods=["POST"])
    def edge_result(task_id: str):
        data = request.get_json(force=True, silent=True) or {}
        r = submit_result(task_id, str(data.get("node_id", "")), data.get("resultado"))
        return jsonify(r), (200 if r.get("ok") else 404)

    @app.route("/api/edge/status")
    def edge_status():
        return jsonify(estado())


# ── CLI ──────────────────────────────────────────────────────────


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Pixel Edge Node (servidor)")
    sub = parser.add_subparsers(dest="cmd")

    p_d = sub.add_parser("dispatch", help="Encolar tarea")
    p_d.add_argument("tipo", choices=sorted(COSTE_TAREA))
    p_d.add_argument("payload", nargs="?", default="{}")
    p_d.add_argument("--prioridad", type=int, default=2)

    p_n = sub.add_parser("next", help="Reclamar siguiente (simula worker)")
    p_n.add_argument("node_id")
    p_n.add_argument("--bateria", type=int, default=None)
    p_n.add_argument("--cargando", action="store_true")

    sub.add_parser("status", help="Foto de la cola")

    args = parser.parse_args(argv)
    if args.cmd == "dispatch":
        print(
            json.dumps(
                dispatch_task(args.tipo, json.loads(args.payload), args.prioridad),
                indent=2,
                ensure_ascii=False,
            )
        )
    elif args.cmd == "next":
        print(
            json.dumps(
                next_task(args.node_id, args.bateria, args.cargando), indent=2, ensure_ascii=False
            )
        )
    elif args.cmd == "status":
        print(json.dumps(estado(), indent=2, ensure_ascii=False))
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Edge worker (idea #2) — corre EN EL TELEFONO (Termux) o en PC.

Hace polling a /api/edge/tasks/next, ejecuta segun capacidad real y
reporta. Cada ejecutor declara lo que puede: sin Termux:API o sin el
binario necesario devuelve `no_soportado` con el motivo (capability
matrix en docs/EDGE-NODE.md). Nada se finge.

Se sincroniza a phone_deploy/ via scripts/sync_phone_deploy.py.
Solo depende de stdlib + requests + safe_exec (tambien en el telefono).

Uso (Termux):
  python edge_worker.py --server http://100.111.139.106:5000 --interval 15
Uso (PC, simula un nodo):
  python edge_worker.py --server http://localhost:5000 --once
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import socket
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    from bridges.comms.safe_exec import run_cmd
except ImportError:
    run_cmd = None  # type: ignore


def _termux(cmd: list, timeout: int = 30) -> Optional[dict]:
    """Ejecuta un comando Termux:API sin shell. None si no existe/falla."""
    if run_cmd is None:
        return None
    try:
        r = run_cmd(cmd, timeout=timeout)
    except Exception:
        return None
    if r.returncode == 127:
        return None
    if r.returncode != 0 or not (r.stdout or "").strip():
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"_raw": r.stdout.strip()}


def _bateria() -> tuple:
    """(pct|None, cargando: bool) via termux-battery-status si existe."""
    info = _termux(["termux-battery-status"], timeout=10) or {}
    pct = info.get("percentage")
    estado = str(info.get("status", "")).upper()
    return (pct if isinstance(pct, (int, float)) else None,
            estado in ("CHARGING", "FULL"))


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ── Ejecutores por tipo ──────────────────────────────────────────

def ex_estado_nodo(payload: dict) -> dict:
    info: Dict[str, Any] = {"status": "ok", "nodo": platform.node(),
                            "sistema": platform.system(),
                            "termux": bool(Path("/data/data/com.termux").exists())}
    bat = _termux(["termux-battery-status"], timeout=10)
    if bat:
        info["bateria"] = bat
    return info


def ex_chequeo_geofence(payload: dict) -> dict:
    try:
        lat, lon, radio = float(payload["lat"]), float(payload["lon"]), float(payload.get("radio_m", 100))
    except (KeyError, ValueError, TypeError):
        return {"status": "error", "error": "payload necesita lat, lon, radio_m"}
    ubi = _termux(["termux-location", "-p", "network", "-r", "once"], timeout=45)
    if not ubi or "latitude" not in ubi:
        return {"status": "no_soportado",
                "motivo": "sin termux-location (fuera de Termux o sin permiso GPS)"}
    dist = _haversine_m(lat, lon, float(ubi["latitude"]), float(ubi["longitude"]))
    return {"status": "ok", "dentro": dist <= radio,
            "distancia_m": round(dist, 1), "radio_m": radio}


def ex_foto_camara(payload: dict) -> dict:
    destino = str(Path(tempfile.gettempdir()) / f"edge_{int(time.time())}.jpg")
    if run_cmd is None:
        return {"status": "no_soportado", "motivo": "sin safe_exec"}
    r = run_cmd(["termux-camera-photo", "-c", str(payload.get("camara", 0)), destino],
                timeout=60)
    if r.returncode == 127:
        return {"status": "no_soportado", "motivo": "sin termux-camera-photo"}
    if r.returncode != 0 or not Path(destino).exists():
        return {"status": "error", "error": (r.stderr or "")[:200]}
    return {"status": "ok", "fichero": destino,
            "bytes": Path(destino).stat().st_size}


def ex_transcribir_voz(payload: dict) -> dict:
    segundos = min(int(payload.get("segundos", 10)), 30)
    destino = str(Path(tempfile.gettempdir()) / f"edge_{int(time.time())}.m4a")
    if run_cmd is None:
        return {"status": "no_soportado", "motivo": "sin safe_exec"}
    r = run_cmd(["termux-microphone-record", "-d",
                 str(Path(destino).parent), "-f", Path(destino).name,
                 "-l", str(segundos)], timeout=segundos + 30)
    if r.returncode == 127:
        return {"status": "no_soportado", "motivo": "sin termux-microphone-record"}
    if r.returncode != 0:
        return {"status": "error", "error": (r.stderr or "")[:200]}
    # V1: grabacion real; STT requiere motor externo (no fingimos texto).
    return {"status": "grabado_sin_stt", "fichero": destino,
            "segundos": segundos,
            "nota": "audio real; transcripcion pendiente de motor STT"}


def ex_ocr_factura(payload: dict) -> dict:
    imagen = str(payload.get("imagen", ""))
    if not imagen or not Path(imagen).exists():
        return {"status": "error", "error": "payload.imagen inexistente"}
    if run_cmd is None:
        return {"status": "no_soportado", "motivo": "sin safe_exec"}
    r = run_cmd(["tesseract", imagen, "stdout", "-l", "spa+eng"], timeout=120)
    if r.returncode == 127:
        return {"status": "no_soportado",
                "motivo": "sin motor OCR (tesseract no instalado)",
                "imagen": imagen, "bytes": Path(imagen).stat().st_size}
    if r.returncode != 0:
        return {"status": "error", "error": (r.stderr or "")[:200]}
    return {"status": "ok", "texto": (r.stdout or "")[:4000]}


EJECUTORES = {
    "estado_nodo": ex_estado_nodo,
    "chequeo_geofence": ex_chequeo_geofence,
    "foto_camara": ex_foto_camara,
    "transcribir_voz": ex_transcribir_voz,
    "ocr_factura": ex_ocr_factura,
}


# ── Bucle worker ─────────────────────────────────────────────────

def una_tarea(server: str, node_id: str) -> dict:
    """Pide, ejecuta y reporta UNA tarea. Devuelve el resultado."""
    if requests is None:
        return {"ok": False, "error": "falta requests (pip install requests)"}
    pct, cargando = _bateria()
    params = {"node_id": node_id}
    if pct is not None:
        params["bateria"] = pct
    if cargando:
        params["cargando"] = "1"
    try:
        nxt = requests.get(f"{server}/api/edge/tasks/next", params=params, timeout=30).json()
    except Exception as e:
        return {"ok": False, "error": f"servidor inalcanzable: {e}"}
    if not nxt.get("ok"):
        return {"ok": True, "hold": nxt.get("hold", "?")}
    ejecutor = EJECUTORES.get(nxt.get("tipo", ""), lambda p: {"status": "error",
                                                              "error": "tipo sin ejecutor"})
    try:
        resultado = ejecutor(nxt.get("payload") or {})
    except Exception as e:
        resultado = {"status": "error", "error": str(e)[:300]}
    try:
        resp = requests.post(
            f"{server}/api/edge/tasks/{nxt['task_id']}/result",
            json={"node_id": node_id, "resultado": resultado}, timeout=30).json()
        return {"ok": bool(resp.get("ok")), "task_id": nxt["task_id"],
                "resultado": resultado}
    except Exception as e:
        return {"ok": False, "error": f"no se pudo reportar: {e}",
                "task_id": nxt.get("task_id")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Edge worker (telefono/PC)")
    parser.add_argument("--server", default="http://localhost:5000")
    parser.add_argument("--node", default=socket.gethostname())
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)

    print(f"edge worker '{args.node}' -> {args.server}")
    while True:
        r = una_tarea(args.server, args.node)
        print(json.dumps(r, ensure_ascii=False, default=str)[:300])
        if args.once:
            return 0 if r.get("ok") else 1
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    sys.exit(main())
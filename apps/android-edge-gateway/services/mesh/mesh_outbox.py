#!/usr/bin/env python3
"""Mesh Offline-First (Fase 3, idea #3) — cola local cifrada para despachos
con mala red. Sync de documentos/estado cuando hay WiFi.

- **Offline-first**: al encolar se aplica en local INMEDIATAMENTE
  (las lecturas funcionan sin red) y se guarda cifrado en el outbox.
- **Cifrado**: Silicon Vault (misma PIN-convencion: MESH_VAULT_PIN o
  DANIELA_PIN). Sin desbloqueo NO se encola (fail-closed). Documentos
  troceados a 6000 chars (limite del vault).
- **Drain**: con red, empuja ops al peer (mesh `sincronizar`) y entrega
  documentos al `RECEIVED_DIR` de file_sync. Marca drenados.
- **Red**: termux-wifi en el Pixel; si no, probe TCP al primer peer;
  sin peers = offline salvo fichero `forzar_online` (tests/dev).

Ops: mesh_set {key, valor}, mesh_add {key, valor}, mesh_counter {key,
delta}, documento {nombre, b64, sha256}.

CLI: python mesh_outbox.py estado|encolar '<json>'|drenar [--pin X]
Rutas: GET /api/mesh/outbox/estado, POST /api/mesh/outbox/encolar,
POST /api/mesh/outbox/drenar
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:
    from flask import jsonify, request
except ImportError:  # pragma: no cover
    jsonify = None  # type: ignore
    request = None  # type: ignore

from core.autonomy.daniela_mesh import get_instance as mesh_instance

from paths import DATA_DIR

OUTBOX_LOG = DATA_DIR / "mesh" / "outbox.jsonl"
FORZAR_FILE = DATA_DIR / "mesh" / "forzar_online"

CHUNK = 6000
MAX_DOC_BYTES = 2 * 1024 * 1024

TIPOS_OP = ("mesh_set", "mesh_add", "mesh_counter", "documento")


def _pin_vault() -> str:
    return (os.getenv("MESH_VAULT_PIN") or os.getenv("DANIELA_PIN") or "").strip()


def _vault() -> Any:
    from services.security.silicon_vault import get_instance as vault_instance

    return vault_instance()


def _asegurar_vault(pin: str = "") -> Any:
    """Devuelve vault desbloqueado o lanza VaultError honesto."""
    v = _vault()
    if getattr(v, "desbloqueada", False):
        return v
    clave = (pin or _pin_vault()).strip()
    if not clave:
        raise RuntimeError("vault bloqueado: define MESH_VAULT_PIN o desbloquea primero")
    if not v.desbloquear(clave):
        raise RuntimeError("vault: PIN incorrecto")
    return v


def _anexar(evento: Dict[str, Any]) -> None:
    try:
        OUTBOX_LOG.parent.mkdir(parents=True, exist_ok=True)
        evento = dict(evento)
        evento.setdefault("ts", datetime.now().isoformat())
        with open(OUTBOX_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _leer_outbox(max_lines: int = 2000) -> List[Dict[str, Any]]:
    if not OUTBOX_LOG.exists():
        return []
    try:
        lines = OUTBOX_LOG.read_text(encoding="utf-8").splitlines()[-max_lines:]
    except OSError:
        return []
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _pendientes() -> List[Dict[str, Any]]:
    drenados = set()
    cola: Dict[str, Any] = {}
    for e in _leer_outbox():
        if e.get("ev") == "encolado" and e.get("op_id"):
            cola[e["op_id"]] = e
        elif e.get("ev") == "drenado" and e.get("op_id"):
            drenados.add(e["op_id"])
    return [cola[k] for k in cola if k not in drenados]


# ── Red ──────────────────────────────────────────────────────────


def _wifi_termux() -> Optional[bool]:
    """True/False si Termux:API responde; None si no hay Termux."""
    try:
        from bridges.comms.safe_exec import run_cmd
    except ImportError:
        return None
    try:
        r = run_cmd(["termux-wifi-connectioninfo"], timeout=10)
    except Exception:
        return None
    if r.returncode == 127:
        return None
    if r.returncode != 0:
        return None
    try:
        info = json.loads(r.stdout or "{}")
    except ValueError:
        return None
    estado = str(info.get("connection_state", info.get("supplicant_state", ""))).upper()
    if not estado:
        return None
    return estado in ("CONNECTED", "COMPLETED")


def _tcp_vivo(url: str, timeout_s: float = 3.0) -> bool:
    try:
        u = urlparse(url if "://" in url else "http://" + url)
        with socket.create_connection((u.hostname or "127.0.0.1", u.port or 80), timeout=timeout_s):
            return True
    except Exception:
        return False


def hay_red() -> Dict[str, Any]:
    """Hay conectividad para sincronizar? Orden: forzar > termux > peer."""
    if FORZAR_FILE.exists():
        return {"online": True, "via": "forzar_online (tests/dev)"}
    tw = _wifi_termux()
    if tw is True:
        return {"online": True, "via": "termux-wifi"}
    try:
        peers = list(mesh_instance().peers or [])
    except Exception:
        peers = []
    for p in peers:
        if _tcp_vivo(p):
            return {"online": True, "via": f"peer {p}"}
    if tw is False:
        return {"online": False, "via": "termux-wifi desconectado"}
    return {"online": False, "via": "sin peers alcanzables"}


# ── Cola ─────────────────────────────────────────────────────────


def _cifrar_partes(v: Any, op_id: str, texto_b64: str) -> int:
    """Guarda el payload troceado en el vault. Devuelve nº de partes."""
    for i in range(0, len(texto_b64), CHUNK):
        parte = texto_b64[i : i + CHUNK]
        if not v.guardar(f"mesh_{op_id}_{i // CHUNK}", parte):
            raise RuntimeError(f"vault rechazo la parte {i // CHUNK}")
    return (len(texto_b64) + CHUNK - 1) // CHUNK


def _descifrar_partes(v: Any, op_id: str, partes: int) -> str:
    trozos = []
    for i in range(partes):
        val = v.leer(f"mesh_{op_id}_{i}")
        if val is None:
            raise RuntimeError(f"falta la parte {i} en el vault")
        trozos.append(val)
    return "".join(trozos)


def encolar(op: Dict[str, Any], pin: str = "") -> Dict[str, Any]:
    """Aplica en local + guarda cifrado. Fail-closed sin vault."""
    kind = (op or {}).get("kind", "")
    if kind not in TIPOS_OP:
        return {"ok": False, "error": f"kind invalido (validos: {sorted(TIPOS_OP)})"}
    if kind == "documento":
        for campo in ("nombre", "b64"):
            if not (op.get(campo) or ""):
                return {"ok": False, "error": f"documento necesita {campo}"}
        try:
            raw = base64.b64decode(op["b64"])
        except Exception:
            return {"ok": False, "error": "b64 invalido"}
        if len(raw) > MAX_DOC_BYTES:
            return {"ok": False, "error": f"documento > {MAX_DOC_BYTES} bytes (v1)"}
    try:
        v = _asegurar_vault(pin)
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}

    op_id = f"op-{int(time.time() * 1000)}"
    cuerpo = json.dumps(op, ensure_ascii=False, default=str)
    try:
        partes = _cifrar_partes(v, op_id, base64.b64encode(cuerpo.encode("utf-8")).decode())
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}

    # Offline-first: aplicar en local YA (lecturas sin red funcionan).
    aplicado = _aplicar_local(op)
    _anexar(
        {
            "ev": "encolado",
            "op_id": op_id,
            "kind": kind,
            "partes": partes,
            "aplicado_local": aplicado,
            "resumen": str(op.get("nombre") or op.get("key", ""))[:80],
        }
    )
    return {"ok": True, "op_id": op_id, "partes": partes, "aplicado_local": aplicado}


def _aplicar_local(op: Dict[str, Any]) -> bool:
    """Aplica la operacion al estado mesh local (o valida documento)."""
    try:
        nodo = mesh_instance()
        kind = op.get("kind")
        if kind == "mesh_set":
            return bool(nodo.set_lww(str(op.get("key", "")), op.get("valor")))
        if kind == "mesh_add":
            nodo.orset_add(str(op.get("key", "")), op.get("valor"))
            return True
        if kind == "mesh_counter":
            nodo.pn_add(str(op.get("key", "")), int(op.get("delta", 1)))
            return True
        if kind == "documento":
            raw = base64.b64decode(op.get("b64", ""))
            digest = hashlib.sha256(raw).hexdigest()
            return digest == (op.get("sha256") or digest)
        return False
    except Exception:
        return False


def drenar(pin: str = "") -> Dict[str, Any]:
    """Con red: empuja ops a peers y entrega documentos. Sin red: hold."""
    red = hay_red()
    if not red["online"]:
        return {"ok": True, "drenadas": 0, "hold": True, "motivo": f"sin red ({red['via']})"}
    pendientes = _pendientes()
    if not pendientes:
        return {"ok": True, "drenadas": 0, "via": red["via"]}
    try:
        v = _asegurar_vault(pin)
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}

    drenadas, entregados, fallos = 0, [], []
    try:
        nodo = mesh_instance()
        remotos = nodo.sincronizar()
    except Exception as e:
        remotos = {"ok": False, "error": str(e)[:160]}
    for item in pendientes:
        try:
            texto = _descifrar_partes(v, item["op_id"], int(item.get("partes", 0)))
            op = json.loads(base64.b64decode(texto.encode()).decode("utf-8"))
        except Exception as e:
            fallos.append({"op_id": item["op_id"], "error": f"descifrado: {e}"[:160]})
            continue
        if op.get("kind") == "documento":
            r = _entregar_documento(op)
            if not r["ok"]:
                fallos.append({"op_id": item["op_id"], **r})
                continue
            entregados.append(op.get("nombre", "?"))
        _anexar({"ev": "drenado", "op_id": item["op_id"], "kind": op.get("kind", "")})
        drenadas += 1
    out = {
        "ok": not fallos,
        "drenadas": drenadas,
        "via": red["via"],
        "documentos": entregados,
        "remoto": remotos,
    }
    if fallos:
        out["fallos"] = fallos
    try:
        from aig.memory.vault import MemoryVault

        MemoryVault().record(
            "mesh/drenajes",
            f"Drenaje via {red['via']}: {drenadas} ops, "
            f"{len(entregados)} documentos, {len(fallos)} fallos.",
        )
    except Exception:
        pass
    return out


def _entregar_documento(op: Dict[str, Any]) -> Dict[str, Any]:
    """Escribe los bytes al RECEIVED_DIR de file_sync (con sha)."""
    try:
        from core.autonomy.file_sync_daemon import RECEIVED_DIR

        raw = base64.b64decode(op.get("b64", ""))
        digest = hashlib.sha256(raw).hexdigest()
        if op.get("sha256") and op["sha256"] != digest:
            return {"ok": False, "error": "sha256 no coincide (corrupto?)"}
        Path(RECEIVED_DIR).mkdir(parents=True, exist_ok=True)
        nombre = Path(str(op.get("nombre", "doc"))).name or "doc"
        destino = Path(RECEIVED_DIR) / f"mesh_{int(time.time())}_{nombre}"
        destino.write_bytes(raw)
        return {"ok": True, "fichero": str(destino), "bytes": len(raw)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def estado() -> Dict[str, Any]:
    """Foto: red, vault, pendientes."""
    try:
        v = _vault()
        vault = "desbloqueado" if getattr(v, "desbloqueada", False) else "bloqueado"
    except Exception:
        vault = "no disponible"
    pend = _pendientes()
    return {
        "ok": True,
        "red": hay_red(),
        "vault": vault,
        "pendientes": len(pend),
        "pendientes_detalle": [
            {
                "op_id": p["op_id"],
                "kind": p.get("kind", "?"),
                "resumen": p.get("resumen", ""),
                "ts": p.get("ts", ""),
            }
            for p in pend[-10:]
        ],
    }


# ── Rutas Flask ──────────────────────────────────────────────────


def register_outbox_routes(app) -> None:
    """Outbox offline-first: estado, encolar, drenar."""

    @app.route("/api/mesh/outbox/estado")
    def outbox_estado():
        return jsonify(estado())

    @app.route("/api/mesh/outbox/encolar", methods=["POST"])
    def outbox_encolar():
        data = request.get_json(force=True, silent=True) or {}
        r = encolar(data.get("op") or data, data.get("pin", ""))
        return jsonify(r), (200 if r.get("ok") else 400)

    @app.route("/api/mesh/outbox/drenar", methods=["POST"])
    def outbox_drenar():
        data = request.get_json(force=True, silent=True) or {}
        r = drenar(data.get("pin", ""))
        return jsonify(r), (200 if r.get("ok") else 400)


# ── CLI ──────────────────────────────────────────────────────────


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mesh Offline-First outbox")
    parser.add_argument("--pin", default="", help="PIN del vault (o MESH_VAULT_PIN)")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("estado", help="Red, vault y pendientes")

    p_q = sub.add_parser("encolar", help="Encolar op JSON")
    p_q.add_argument("op_json")

    sub.add_parser("drenar", help="Drenar con red")

    args = parser.parse_args(argv)
    pin = args.pin or os.getenv("MESH_VAULT_PIN", "")
    if args.cmd == "estado":
        print(json.dumps(estado(), indent=2, ensure_ascii=False))
    elif args.cmd == "encolar":
        print(json.dumps(encolar(json.loads(args.op_json), pin), indent=2, ensure_ascii=False))
    elif args.cmd == "drenar":
        print(json.dumps(drenar(pin), indent=2, ensure_ascii=False))
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Artemis Bridge — Daniela <-> google/artemis (sidecar, ADR-018)
===============================================================
ARTEMIS automatiza un Android real a partir de instrucciones en lenguaje
natural (CLI `artemis run`, consola web en :8000, servidor MCP). En este repo
es SIDEcar: se instala y arranca fuera del arbol de dependencias:

    cd sidecars/artemis && ./start.sh        # o start.bat en Windows
    uv run artemis status                     # su propio CLI

Este modulo es la **frontera**: no importa nada de `sidecars/artemis/` ni
instala `artemis` como dependencia; solo habla HTTP con el daemon. Si Google
cambia por dentro, esto sigue funcionando (mismo patron que
`engine/gev_bridge.py`).

Rutas verificadas contra `packages/artemis-client/src/artemis_client/client.py`
(pinned 351ca84, 2026-10-04):

  GET  /api/status            salud del daemon
  GET  /api/devices           dispositivos ADB visibles para el host
  POST /api/run               {goal, profile, session_id, ingress,
                               device_serial?} -> {status, tasks:[{task_id}]}
  GET  /api/sessions/<id>     estado/resultado de la tarea
  POST /api/stop              {session_id}      -> {status: stopped}

Perfiles: `flash` (reaccivo, ~3-5 s/paso) y `pro` (planificador + verificador).
Estados terminales/exitosos: mismos que artemis_client.models
(TERMINAL_TASK_STATUSES / SUCCESS_TASK_STATUSES).

Config por entorno:
  ARTEMIS_BASE_URL   ej. http://127.0.0.1:8000 (o ARTEMIS_DAEMON_HOST/PORT)
  ARTEMIS_TOKEN      opcional; si existe se manda Authorization: Bearer
  ARTEMIS_TIMEOUT    timeout por peticion en segundos (30)

Nunca imprime ni propaga el token. Coste: $0 (todo local).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from collections.abc import Sequence
from typing import Any

import requests

USER_AGENT = "DanielaOS-Artemis-Bridge/1.0"
REQUEST_TIMEOUT = int(os.getenv("ARTEMIS_TIMEOUT", "30"))

# Estados copiados de artemis_client.models (sidecar): no los inventamos aqui.
ESTADOS_TERMINALES = frozenset(
    {"completed", "success", "failed", "cancelled", "canceled", "rejected"}
)
ESTADOS_OK = frozenset({"completed", "success"})
PERFILES = ("flash", "pro")


def _base_por_defecto() -> str:
    explicita = os.getenv("ARTEMIS_BASE_URL", "").strip()
    if explicita:
        return explicita.rstrip("/")
    host = os.getenv("ARTEMIS_DAEMON_HOST", "127.0.0.1")
    puerto = os.getenv("ARTEMIS_DAEMON_PORT", "8000")
    return f"http://{host}:{puerto}"


class ArtemisClient:
    """Cliente HTTP del daemon de ARTEMIS. Solo stdlib + requests.

    Un lado puede morirse sin tumbar nada del otro (ADR-018: el health gate
    propio es el criterio de verdad, no el estado del sidecar).
    """

    def __init__(
        self,
        base: str | None = None,
        token: str | None = None,
        timeout: int = REQUEST_TIMEOUT,
    ):
        self.base = (base or _base_por_defecto()).rstrip("/")
        self.timeout = timeout
        self._s = requests.Session()
        self._s.headers.update({"User-Agent": USER_AGENT})
        resuelto = token if token is not None else os.getenv("ARTEMIS_TOKEN", "")
        if resuelto:
            self._s.headers.update({"Authorization": f"Bearer {resuelto}"})

    # -- infraestructura --

    def _json(
        self,
        metodo: str,
        ruta: str,
        cuerpo: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> Any:
        url = f"{self.base}{ruta}"
        r = self._s.request(
            metodo, url, json=cuerpo, timeout=timeout or self.timeout
        )
        r.raise_for_status()
        if not r.content:
            return {}
        return r.json()

    def is_up(self) -> bool:
        """True si el daemon de ARTEMIS responde. Nunca lanza.

        Exige 200 + JSON: en el puerto 8000 puede haber cualquier otro
        servidor (2026-10-04: un `http.server` de ficheros respondia 404 y
        un `<500` ingenuo daba falso positivo).
        """
        try:
            r = self._s.get(f"{self.base}/api/status", timeout=5)
            if r.status_code != 200:
                return False
            return isinstance(r.json(), dict)
        except Exception:
            return False

    def dispositivos(self) -> list[dict[str, Any]]:
        """Dispositivos Android que el host de ARTEMIS ve por ADB."""
        payload = self._json("GET", "/api/devices")
        if isinstance(payload, dict):
            crudos = payload.get("devices", [])
        else:
            crudos = payload
        return [d for d in crudos or [] if isinstance(d, dict)]

    # -- ejecucion --

    def ejecutar(
        self,
        meta: str,
        perfil: str = "flash",
        serial: str | None = None,
        espera: float = 600.0,
        intervalo: float = 2.0,
    ) -> dict[str, Any]:
        """Envia una tarea y espera su resultado terminal.

        Devuelve siempre un dict con claves:
          ok         True solo si el estado final es completed/success
          task_id    identificador de la tarea (session_id)
          estado     estado final (o "timeout")
          output     salida que devolvio el agente (si la hay)
          error      mensaje de error (si lo hay)
          meta, perfil, base
        """
        meta = (meta or "").strip()
        if not meta:
            return {"ok": False, "error": "meta vacia"}
        if perfil not in PERFILES:
            return {"ok": False, "error": f"perfil desconocido: {perfil!r}"}

        task_id = str(uuid.uuid4())
        cuerpo: dict[str, Any] = {
            "goal": meta,
            "profile": perfil,
            "session_id": task_id,
            "ingress": "daniela_bridge",
        }
        if serial:
            cuerpo["device_serial"] = serial

        base = {
            "task_id": task_id,
            "meta": meta,
            "perfil": perfil,
            "base": self.base,
        }
        try:
            admision = self._json("POST", "/api/run", cuerpo)
        except Exception as exc:  # daemon caido, red, 500
            return {**base, "ok": False, "error": f"sin respuesta: {exc}"}

        estado_admision = str(admision.get("status") or "").lower()
        tareas = admision.get("tasks")
        if estado_admision == "rejected" or not tareas:
            detalle = admision.get("error") or "ARTEMIS rechazo la tarea"
            return {**base, "ok": False, "error": str(detalle)}

        primero = tareas[0] if isinstance(tareas[0], dict) else {}
        task_id = str(
            primero.get("task_id") or primero.get("session_id") or task_id
        )

        limite = time.monotonic() + max(1.0, espera)
        ultimo: dict[str, Any] = {"status": "launching"}
        ultimo_fallo = ""
        while time.monotonic() < limite:
            # El daemon tarda en crear la fila de sesion (medido: 13 s) y un
            # 404/timeout puntual no es un fallo: se reintenta hasta el
            # deadline. El ultimo error se conserva por si expira.
            try:
                ultimo = self._json("GET", f"/api/sessions/{task_id}")
                ultimo_fallo = ""
            except Exception as exc:
                ultimo_fallo = str(exc)
            estado = str(ultimo.get("status") or "").lower()
            if estado in ESTADOS_TERMINALES:
                ok = estado in ESTADOS_OK
                return {
                    **base,
                    "task_id": task_id,
                    "ok": ok,
                    "estado": estado,
                    "output": ultimo.get("output"),
                    "error": ultimo.get("error"),
                    "turns": ultimo.get("turns"),
                }
            time.sleep(intervalo)

        return {
            **base,
            "task_id": task_id,
            "ok": False,
            "estado": "timeout",
            "error": (
                f"sin estado terminal en {espera:.0f}s"
                + (f" (ultimo fallo: {ultimo_fallo})" if ultimo_fallo else "")
            ),
        }

    def parar(self, task_id: str) -> bool:
        """Pide cancelar una tarea. True si el daemon la dio por parada."""
        try:
            payload = self._json("POST", "/api/stop", {"session_id": task_id})
        except Exception:
            return False
        return str(payload.get("status") or "").lower() == "stopped"


# -- CLI --------------------------------------------------------------------


def _main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Puente Daniela <-> ARTEMIS (sidecar)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("estado", help="comprobar si el daemon responde")
    sub.add_parser("dispositivos", help="dispositivos ADB visibles")

    r = sub.add_parser("run", help="ejecutar una instruccion en el dispositivo")
    r.add_argument("meta")
    r.add_argument("--perfil", default="flash", choices=PERFILES)
    r.add_argument("--serial", default=None)
    r.add_argument("--espera", type=float, default=600.0)

    s = sub.add_parser("stop", help="cancelar una tarea")
    s.add_argument("task_id")

    args = p.parse_args(argv)
    cli = ArtemisClient()

    if args.cmd == "estado":
        up = cli.is_up()
        print(f"ARTEMIS en {cli.base}: {'ARRIBA' if up else 'CAIDO'}")
        return 0 if up else 1

    if args.cmd == "dispositivos":
        for d in cli.dispositivos():
            serial = d.get("serial") or d.get("device_serial") or "?"
            print(serial)
        return 0

    if args.cmd == "run":
        res = cli.ejecutar(
            args.meta, perfil=args.perfil, serial=args.serial, espera=args.espera
        )
        print(res)
        return 0 if res.get("ok") else 1

    if args.cmd == "stop":
        return 0 if cli.parar(args.task_id) else 1

    return 2


if __name__ == "__main__":
    sys.exit(_main())

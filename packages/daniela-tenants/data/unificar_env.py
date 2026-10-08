#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unifica .env con .env.master sin perder lo que el usuario acaba de cambiar.

Reglas, en este orden de prioridad (la ultima gana, que es como parsea
python-dotenv: si una clave aparece dos veces, manda la de abajo):

  1. TODO el contenido de .env.master (639 variables de la infraestructura).
  2. Un bloque final de SOBREESCRITURAS con lo que hay hoy en .env:
     el PIN nuevo y la API key nueva. Sin esto, las claves viejas del master
     (lineas 69, 279 y 320) ganarian y volveriamos al punto de partida.
  3. BASE_GEMINI se iguala a la key nueva: el master hace
     GEMINI_API_KEY=${BASE_GEMINI}, asi que dejar el BASE_GEMINI viejo
     dejaria una clave caducada alimentando todo lo que la referencie.
"""

from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENV = RAIZ / ".env"
MASTER = RAIZ / ".env.master"

VAR = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def leer_vars(ruta: Path) -> "list[tuple[str, str]]":
    """Devuelve (clave, valor) conservando el orden del fichero."""
    out = []
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        m = VAR.match(linea.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def main() -> int:
    if not ENV.exists() or not MASTER.exists():
        print("Falta .env o .env.master")
        return 1

    actuales = leer_vars(ENV)
    if not actuales:
        print(".env esta vacio: no sigo, no quiero sobrescribirlo con nada")
        return 1

    # --- copia de seguridad ------------------------------------------------
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    copia = RAIZ / f".env.bak_{sello}"
    shutil.copy2(ENV, copia)
    print(f"copia de seguridad -> {copia.name}")

    maestro = MASTER.read_text(encoding="utf-8", errors="replace")
    gemini = next((v for k, v in actuales if k == "GEMINI_API_KEY"), "")

    # --- escribir ----------------------------------------------------------
    piezas = [
        "#" * 78,
        "# .env UNIFICADO — generado el " + datetime.now().strftime("%Y-%m-%d %H:%M"),
        "#",
        "# Estructura (python-dotenv: si una clave se repite, manda la de MAS ABAJO):",
        "#   1. .env.master completo  -> 639 variables de la infraestructura aig",
        "#   2. SOBREESCRITURAS       -> el PIN y la API key que has puesto tu",
        "#",
        "# No subir a git. .gitignore ya lo cubre, pero no esta de mas decirlo.",
        "#" * 78,
        "",
        maestro.rstrip(),
        "",
        "#" * 78,
        "# SOBREESCRITURAS — tus valores actuales. Ganan a todo lo de arriba.",
        "#" * 78,
        "",
    ]
    for k, v in actuales:
        piezas.append(f"{k}={v}")

    # BASE_GEMINI alimenta GEMINI_API_KEY=${BASE_GEMINI} en el master: si se
    # queda con la clave vieja, todo lo que la referencie seguira caducado.
    if gemini:
        piezas += [
            "",
            "# El master hace GEMINI_API_KEY=${BASE_GEMINI}: se iguala a la key nueva",
            "# para que ninguna referencia indirecta use la caducada.",
            f"BASE_GEMINI={gemini}",
            "",
        ]

    ENV.write_text("\n".join(piezas) + "\n", encoding="utf-8")

    # --- informe -----------------------------------------------------------
    despues = leer_vars(ENV)
    print(f"variables antes   : {len(actuales)}")
    print(f"variables despues : {len(set(k for k, _ in despues))} unicas")
    for k in ("DANIELA_PIN", "GEMINI_API_KEY", "BASE_GEMINI"):
        v = next((val for clave, val in despues if clave == k), "")
        if k == "DANIELA_PIN":
            print(f"  {k:16s} longitud {len(v)}")
        else:
            print(f"  {k:16s} {v[:14]}... ({len(v)} caracteres)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Puerta de tests: ademas de correrlos, comprueba que se recogen TODOS.

⚠️ POR QUE EXISTE ESTE FICHERO
------------------------------
`pytest tests/ -q` puede quedar en verde habiendo probado la mitad del repo.
`MEMORY.md` ya documenta dos formas de que eso pase en este proyecto:

  - `norecursedirs` mal puesto: pytest define una lista por defecto, y
    declararla la SUSTITUYE en lugar de ampliarla.
  - un `pytest.skip` por una ruta que un refactor movio: el test deja de
    comprobar nada **en silencio** y la suite sigue verde.

En los dos casos el sintoma es el mismo: **se recogen menos tests**. Ejecutar y
contar no basta; hay que exigir el numero.

Linea base medida el 2026-09-25: **1204 tests**, 0 fallos, 3 skip, 2 xfal.

NOTA PORT (universe): LINEA_BASE=166 es la medida recalibrada para el layout
'universe' donde los tests viven en `packages/*/tests` y `apps/*/services/tests/`.
En el repo legado `aig` la base era 1222 con layout `tests/` en raiz. La base
sale de medir con `--collect-only`, nunca de sumar a mano.

Uso:
    python scripts/core/ci_conteo_tests.py     # 0 = OK, 1 = se recogen menos
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Sube este numero cuando anadas tests. Bajarlo exige justificar QUE se dejo de
# recoger y por que: casi siempre es un fichero que se movio de sitio.
#
# 1204 -> 1219 el 2026-09-25: +8 de tests/core/test_config_ruff_unica.py y
#          +7 de tests/core/test_topologia_puertos_y_rutas.py.
#
# 1219 -> 1217 el mismo dia, AL MEDIRLO EN VEZ DE SUMARLO A MANO.
#          El 1219 se puso sumando "8 + 7" segun lo que declaraban los
#          docstrings de los dos ficheros nuevos, no ejecutando `--collect-only`.
#          Medido de verdad: ruff 8 + topologia 7 = 1217. El 1219 era un numero
#          inventado, y una linea base que no sale de una medida no protege de
#          nada.
#          Leccion: la linea base se fija con el numero que devuelve
#          `--collect-only`, nunca sumando a mano lo que uno cree que anadio.
#
#          1217 YA incluye `test_caddy_sirve_health_en_texto_plano` (el
#          healthcheck de caddy respondia 308 y salia `healthy` igualmente):
#          topologia paso de 7 a 8 funciones a la vez que se corregia el 1219.
#
# 1217 -> 166 el 2026-10-10, al recalibrar la base para el layout universe:
#          Tests recogidos: 166 (de packages/daniela-core/tests/,
#          packages/daniela-obsidian/tests/, packages/daniela-sdk/tests/,
#          apps/mobile-pwa/services/tests/). La base sale de medir con
#          `--collect-only`, nunca de sumar a mano.
#          NOTE: import errors en algunos test files reducen el numero colectado.
# 166 -> 1222 NO APLICA: el repo legado `aig` usa layout `tests/` en raiz.
#          En universe los tests viven dispersos en packages/*/tests y apps/*/services/tests.
LINEA_BASE = 166

# Directorios donde viven los tests en este monorepo:
TEST_DIRS = [
    "packages/*/tests",
    "apps/*/services/tests",
]


def _encontrar_test_dirs() -> list[str]:
    """Find all test directories matching the known patterns."""
    dirs: list[str] = []
    for pattern in TEST_DIRS:
        for path in sorted(Path(__file__).resolve().parent.parent.parent.glob(pattern)):
            if path.is_dir():
                dirs.append(str(path))
    return dirs


def _recogidos() -> int:
    test_dirs = _encontrar_test_dirs()
    if not test_dirs:
        print(
            "No se encontraron directorios de tests con los patrones esperados.",
            file=sys.stderr,
        )
        return 0

    # Construir la lista de argumentos: pytest + dirs + flags
    args = [
        sys.executable,
        "-m",
        "pytest",
    ]
    for d in test_dirs:
        args.append(d)
    args += ["--collect-only", "-q", "-p", "no:cacheprovider"]

    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
    )
    total = 0
    for linea in proc.stdout.splitlines():
        # Formato de `--collect-only -q`: "tests/xxx.py: 12"
        m = re.match(r"^.*:\s*(\d+)\s*$", linea)
        if m:
            total += int(m.group(1))
    if total == 0:
        print(
            "No se recogio ningun test. La colecta fallo:\n"
            + (proc.stdout[-2000:] or "(sin stdout)")
            + (proc.stderr[-2000:] or ""),
            file=sys.stderr,
        )
    return total


def main() -> int:
    total = _recogidos()
    print(f"tests recogidos: {total} (linea base: {LINEA_BASE})")

    if total < LINEA_BASE:
        print(
            f"\nSE RECOGEN MENOS TESTS QUE LA LINEA BASE ({total} < {LINEA_BASE}).\n"
            "Algo impide que ficheros de test se colecten: revisa `norecursedirs`,\n"
            "un import roto, o una ruta que se movio y provoca skips silenciosos.\n"
            "NO baje LINEA_BASE sin identificar que se dejo de recoger.",
            file=sys.stderr,
        )
        return 1

    if total > LINEA_BASE:
        print(
            f"Hay {total - LINEA_BASE} tests mas que la linea base. "
            f"Sube LINEA_BASE a {total} en scripts/core/ci_conteo_tests.py."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
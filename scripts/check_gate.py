"""Compara el pytest actual vs baseline por NOMBRE (nunca por conteo).

Uso: python scripts/check_gate.py
      PYTEST_CURRENT_FILE=<ruta> python scripts/check_gate.py   (fichero propio)
Salida: 0 si no hay fallos nuevos; 1 si los hay (los lista).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASELINE = REPO / ".quality-baseline" / "pytest-failures-2026-10-03.txt"
DEFAULT_CURRENT = Path(os.environ.get("TEMP", ".")) / "pytest-20261004.txt"
CURRENT = Path(os.environ.get("PYTEST_CURRENT_FILE", DEFAULT_CURRENT))

PAT = re.compile(r"^(FAILED|ERROR)\s+(\S+)")


def load(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = PAT.match(line)
        if m:
            # nodo truncado tipo "id - AssertionError..." -> solo el id
            nodeid = m.group(2)
            names.add(f"{m.group(1)} {nodeid}")
    return names


def main() -> int:
    actual = load(CURRENT)
    base = load(BASELINE)
    nuevos = sorted(actual - base)
    resueltos = sorted(base - actual)

    print(f"actual={len(actual)} baseline={len(base)}")
    print(f"NUEVOS = {len(nuevos)} (debe ser 0)")
    for n in nuevos:
        print(f"  + {n}")
    print(f"resueltos vs baseline = {len(resueltos)}")
    if nuevos:
        print("GATE: NO-GO (fallos nuevos)")
        return 1
    print("GATE: GO (0 fallos nuevos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Ratchet de calidad: el techo de deuda de lint no puede subir.

⚠️ POR QUE EXISTE ESTE FICHERO
------------------------------
`.quality-baseline/ruff-count.txt` existe desde el 2026-09-23, va de 10 565 a 0
y esta **documentado** en `docs/CODE-REVIEW.md` §7. Pero el 2026-09-25 se midio:

    $ grep -rn 'ruff-count' .
    docs/CODE-REVIEW.md          <- unica aparicion

**Nadie lo leia.** El ratchet era documentacion, no automatizacion. Y el
fichero decia 0 mientras la realidad daba 33, porque `shared/pyproject.toml`
sombreaba la config de ruff de la raiz (ver `docs/AUDITORIA-2026-09-25.md` §3).

Este script cierra las dos brechas:

  1. Lee el techo y lo compara con la realidad medida con `ruff check .`
     **sin ningun flag** — el mismo comando que documenta CODE-REVIEW.md §7.
     Si divergen, el numero no era reproducible: falla.
  2. Mantiene **presupuesto por regla**. El total es una medida agregada: se
     pueden arreglar 40 F401 y meter 20 BLE001 nuevos y el total "mejora". Con
     presupuesto por regla, ninguna regla puede crecer aunque el total baje.

Uso:
    python scripts/utils/ratchet_ruff.py              # comprueba (para CI)
    python scripts/utils/ratchet_ruff.py --actualizar  # baja el techo si mejoro

Salida: 0 si el techo se respeta, 1 si hay regresion.

Nota sobre coste: invoca `ruff check .` una vez. En esta maquina tarda unos
segundos; no necesita red ni Docker.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE = REPO_ROOT / ".quality-baseline" / "ruff-count.txt"
POR_REGLA = REPO_ROOT / ".quality-baseline" / "ruff-por-regla.json"
HISTORIAL = REPO_ROOT / ".quality-baseline" / "historial.tsv"


def _leer_techo() -> int:
    """Techo actual. Es el ultimo numero del fichero (las demas lineas son historia)."""
    if not BASELINE.is_file():
        raise SystemExit(f"No existe el baseline: {BASELINE}")
    numeros = [
        linea.strip()
        for linea in BASELINE.read_text(encoding="utf-8").splitlines()
        if linea.strip().isdigit()
    ]
    if not numeros:
        raise SystemExit(f"{BASELINE} no contiene ningun numero de techo")
    return int(numeros[-1])


def _leer_presupuesto() -> dict[str, int]:
    if not POR_REGLA.is_file():
        return {}
    return json.loads(POR_REGLA.read_text(encoding="utf-8"))


def _medir() -> tuple[int, dict[str, int]]:
    """Devuelve (total, conteo por regla) ejecutando ruff SIN FLAGS.

    Sin flags es la clave: con `--ignore=` por CLI el numero no es reproducible
    y el techo deja de significar nada (fue el fallo original).
    """
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", ".", "--output-format", "concise"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    por_regla: dict[str, int] = {}
    for linea in proc.stdout.splitlines():
        # Formato: ruta:linea:col: CODIGO mensaje
        m = re.search(r":\s([A-Z]+[0-9]+)\s", linea)
        if m:
            por_regla[m.group(1)] = por_regla.get(m.group(1), 0) + 1

    total = sum(por_regla.values())

    # Coherencia: el total tiene que ser lo que dice ruff, no lo que contamos.
    m = re.search(r"Found (\d+) error", proc.stdout)
    if m and int(m.group(1)) != total:
        print(
            f"AVISO: el parseo conto {total} pero ruff dice {m.group(1)}. "
            "El formato de salida cambio; revisa el parser de este script.",
            file=sys.stderr,
        )
        total = int(m.group(1))

    return total, por_regla


def _anotar_historial(total: int, commit: str) -> None:
    linea = f"{datetime.now(UTC).date().isoformat()}\t{commit}\t{total}\n"
    with HISTORIAL.open("a", encoding="utf-8") as fh:
        fh.write(linea)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--actualizar",
        action="store_true",
        help="baja el techo y el presupuesto al valor medido (solo si mejoro)",
    )
    args = parser.parse_args()

    techo = _leer_techo()
    presupuesto = _leer_presupuesto()
    total, por_regla = _medir()

    commit = (
        subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        or "sin-git"
    )

    print(f"techo (ruff-count.txt) : {techo}")
    print(f"realidad (ruff check .): {total}")
    if presupuesto:
        print(f"presupuesto por regla  : {len(presupuesto)} reglas vigiladas")

    if args.actualizar:
        if total > techo:
            print(
                f"\nNo se puede subir el techo ({techo} -> {total}). "
                "Arregla los hallazgos nuevos o justifica el aumento en el "
                "mismo commit.",
                file=sys.stderr,
            )
            return 1
        BASELINE.write_text(
            BASELINE.read_text(encoding="utf-8").rstrip("\n")
            + f"\n#       -> {total} ({datetime.now(UTC).date().isoformat()}, "
            f"medido sin flags via ratchet_ruff.py).\n{total}",
            encoding="utf-8",
        )
        POR_REGLA.write_text(
            json.dumps(dict(sorted(por_regla.items())), indent=2) + "\n",
            encoding="utf-8",
        )
        _anotar_historial(total, commit)
        print(f"\nTecho y presupuesto actualizados a {total}.")
        return 0

    fallo = False

    if total > techo:
        print(
            f"\nREGRESION: hay {total - techo} hallazgos mas que el techo ({techo}).",
            file=sys.stderr,
        )
        culpables = {k: v for k, v in por_regla.items() if v > presupuesto.get(k, 0)}
        for regla, n in sorted(culpables.items(), key=lambda x: -x[1]):
            antes = presupuesto.get(regla, 0)
            print(f"  {regla}: {antes} -> {n}  (+{n - antes})", file=sys.stderr)
        print(
            "\nArreglalo con:  python -m ruff check . --output-format concise",
            file=sys.stderr,
        )
        fallo = True

    # El presupuesto por regla se comprueba SIEMPRE, aunque el total baje:
    # arreglar 40 F401 y meter 20 BLE001 nuevos seria un "total que mejora"
    # con una regla que empeora.
    for regla, n in sorted(por_regla.items()):
        techo_regla = presupuesto.get(regla)
        if techo_regla is not None and n > techo_regla:
            print(
                f"\nREGRESION por regla: {regla} paso de {techo_regla} a {n} "
                f"(el total puede haber bajado, pero esta regla crecio).",
                file=sys.stderr,
            )
            fallo = True

    if fallo:
        return 1

    if total < techo:
        print(
            f"\nMejora: {total} < techo {techo}. Baja el techo con:\n"
            "  python scripts/utils/ratchet_ruff.py --actualizar"
        )
    else:
        print("\nOK: el techo se respeta y ninguna regla crecio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

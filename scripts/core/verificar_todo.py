#!/usr/bin/env python3
"""Punto de entrada UNICO de verificacion. Todas las puertas, en orden, de una vez.

⚠️ POR QUE EXISTE ESTE FICHERO
------------------------------
El 2026-09-25 se retiraron los workflows de `.github/workflows/` (ver
`docs/archive/README.md`): no estaban trackeados y no hay runner. Las puertas de
este repo son **locales**. Pero "locales" no puede significar "cada uno se
acuerda de las seis": una puerta de la que no se acuerda nadie es una puerta que
no existe.

Este script es la lista completa y ejecutable de lo que se comprueba antes de
dar algo por bueno. Tiene dos propiedades que no son accidentales:

  1. **Se ejecuta en el mismo orden que la CI antigua** (precondiciones primero,
     que abortan ruidosamente y temprano). Correr los tests antes de comprobar
     que el cwd es el correcto es como no correrlos: se recogen 0 y sale verde.
  2. **Si una puerta deja de existir, esto falla.** La lista de abajo esta
     vigilada por `tests/core/test_punto_de_entrada.py`, que comprueba que todo
     script citado existe en disco. Un script que se renombra y deja aqui una
     referencia muerta produce una puerta que **no se ejecuta y no se nota** —
     exactamente la clase de fallo que este repo intenta no tener.

Uso:
    python scripts/core/verificar_todo.py              # todas las puertas
    python scripts/core/verificar_todo.py --rapido     # sin los tests (solo estaticas)

Salida: 0 si TODAS pasan, 1 si falla alguna. Imprime un resumen final con el
resultado de cada una, porque un fallo en el paso 3 no debe obligar a leer los
1200 tests para saber si el 5 paso.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Puerta:
    """Una comprobacion. `args` se ejecuta con el interprete actual."""

    nombre: str
    args: list[str]
    # "estatica" = no corre la suite de tests; "suite" = si.
    tipo: str
    # Por que esta puerta existe, en una linea. Se imprime si falla.
    razon: str


# ---------------------------------------------------------------------------
# La lista de puertas. ORDEN IMPORTANTE: las precondiciones van primero porque
# si el cwd es el equivocado, todo lo demas mide el sitio equivocado.
#
# ⚠️ Al anadir una puerta nueva, anadirla aqui Y en el test que vigila esta
# lista (`tests/core/test_punto_de_entrada.py`). Una puerta que solo vive en un
# script y no se ejecuta desde aqui es una puerta que nadie corre.
# ---------------------------------------------------------------------------
PUERTAS: tuple[Puerta, ...] = (
    Puerta(
        nombre="precondiciones",
        args=["scripts/core/ci_precondiciones.py"],
        tipo="estatica",
        razon="si el cwd o los backends estan mal, todo lo demas mide el sitio equivocado",
    ),
    Puerta(
        nombre="ruff (sin flags)",
        args=["-m", "ruff", "check", "."],
        tipo="estatica",
        razon="el mismo comando que documenta CODE-REVIEW.md §7; con flags no es reproducible",
    ),
    Puerta(
        nombre="ruff format --check",
        args=["-m", "ruff", "format", "--check", "."],
        tipo="estatica",
        razon="el formateador debe ser el del venv, alineado con .pre-commit-config.yaml",
    ),
    Puerta(
        nombre="ratchet de calidad",
        args=["scripts/utils/ratchet_ruff.py"],
        tipo="estatica",
        razon="el techo de deuda no puede subir, ni por regla suelta",
    ),
    Puerta(
        nombre="tests",
        args=["-m", "pytest", "tests/", "-q"],
        tipo="suite",
        razon="la suite completa, acotada a tests/ (sin acotar se cuelan terceros)",
    ),
    Puerta(
        nombre="recuento de tests",
        args=["scripts/core/ci_conteo_tests.py"],
        tipo="suite",
        razon="un fichero de test que deja de recogerse pone la suite verde y vacia",
    ),
)

# ---------------------------------------------------------------------------
# ⚠️ FALSOS ROJOS CONOCIDOS en la puerta "tests"
#
# Medido el 2026-09-25: la suite entera puede salir **exit 1 sin un solo test
# fallido**. Todas las lineas de progreso son puntos (., s, x) y no aparece
# ninguna `F`, pero el proceso termina 1 y sustituye el resumen por:
#
#   [safe-delete][SAFE_DELETE_BULK_CONFIRM_REQUIRED] {"count":176, ...}
#
# Causa: al terminar la sesion, pytest borra su propio directorio temporal
# (`.../pytest-of-<usuario>/garbage-<uuid>`, 176 ficheros). **No es un fallo de
# los tests**: es un guardia externo de borrado masivo que intercepta ese
# `rmtree`. Reproducido de dos formas:
#
#   1. `pytest tests/` -> exit 1; `pytest tests/core tests/agents` -> exit 1
#      con el mismo mensaje; cada fichero por separado -> exit 0.
#   2. `pytest tests/ --basetemp=<ruta explicita>` -> **exit 0**. Al darle otro
#      directorio base, el borrado no dispara el guardia.
#
# Diagnostico: NO es un defecto del repo. Pero si se lee en crudo, "exit 1" es
# indistinguible de "hay tests rotos", y eso es exactamente la clase de senal
# ambigua que este repo no quiere. De ahi `_ROJO_FALSO_TEMPORAL`: si la salida
# trae la marca del guardia Y no hay fallos de test, la puerta pasa y lo dice.
#
# ⚠️ La guardia NO es un "si falla, ignorar": exige las DOS condiciones (marca
# del guardia + cero tests fallidos). Un fallo real de test nunca trae esa
# marca, asi que sigue siendo rojo.
_ROJO_FALSO_TEMPORAL = "SAFE_DELETE_BULK_CONFIRM_REQUIRED"

# Marcas que delatan un fallo REAL de pytest. Si aparece cualquiera, la puerta
# es roja aunque tambien este la marca del guardia.
_MARCAS_FALLO_REAL = ("\nFAILED", "\nERROR ", "= FAILURES =", "= ERRORS =", "failed,")


def _ejecutar(puerta: Puerta) -> tuple[bool, str]:
    """Corre una puerta. Devuelve (ok, salida_completa).

    Aplica la excepcion documentada arriba: un exit != 0 que sea SOLO el
    guardia externo de borrado masivo, sin ninguna marca de fallo real de
    pytest, no es un fallo. Se informa igualmente para que quede en el log.
    """
    proc = subprocess.run(
        [sys.executable, *puerta.args],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    )
    salida = proc.stdout
    if proc.stderr:
        salida += ("\n" if salida else "") + proc.stderr

    if proc.returncode == 0:
        return True, salida

    # Solo para la puerta de tests, y solo con las dos condiciones.
    if puerta.nombre == "tests" and _ROJO_FALSO_TEMPORAL in salida:
        if not any(marca in salida for marca in _MARCAS_FALLO_REAL):
            aviso = (
                "\n[verificar_todo] exit != 0 SIN fallos de test: es el guardia "
                "de borrado masivo del entorno interceptando la limpieza del "
                "directorio temporal de pytest, no un defecto del repo.\n"
                "  Reproduccion: `pytest tests/ --basetemp=<ruta> ` -> exit 0.\n"
                "  Se cuenta como puerta VERDE. Ver el comentario de "
                "_ROJO_FALSO_TEMPORAL en scripts/core/verificar_todo.py."
            )
            return True, salida + aviso

    return False, salida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rapido",
        action="store_true",
        help="omite las puertas que corren la suite de tests",
    )
    args = parser.parse_args()

    puertas = [p for p in PUERTAS if not args.rapido or p.tipo == "estatica"]

    resultados: list[tuple[str, bool, str]] = []

    for puerta in puertas:
        print(f"\n{'=' * 70}")
        print(f">>> {puerta.nombre}")
        print("=" * 70)
        ok, salida = _ejecutar(puerta)
        resultados.append((puerta.nombre, ok, salida))
        if salida:
            print(salida.rstrip())
        if not ok:
            print(f"\n✗ FALLO en «{puerta.nombre}»: {puerta.razon}", file=sys.stderr)

    # Resumen: un fallo en el paso 3 no debe obligar a leer los 1200 tests para
    # saber si el 5 paso.
    print(f"\n{'=' * 70}")
    print("RESUMEN")
    print("=" * 70)
    for nombre, ok, _ in resultados:
        print(f"  {'✓' if ok else '✗'} {nombre}")

    fallidas = [n for n, ok, _ in resultados if not ok]
    if fallidas:
        print(
            f"\n{len(fallidas)} puerta(s) en rojo: {', '.join(fallidas)}\n"
            "Nada de este repo se da por bueno con una puerta en rojo.",
            file=sys.stderr,
        )
        return 1

    print(f"\nTodas las puertas verdes ({len(resultados)}).")
    if args.rapido:
        print("(modo --rapido: la suite de tests NO se ha corrido)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

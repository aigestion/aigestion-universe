#!/usr/bin/env python3
"""Puerta de precondiciones: comprueba lo que la CI va a ASUMIR antes de correrla.

⚠️ POR QUE EXISTE ESTE FICHERO
------------------------------
`ci.yml` declaraba `working-directory: config` en todos los pasos, heredado de
`cd.yml`. Pero `actions/checkout` deja el repo en la raiz del workspace, asi que
cada `run` se ejecutaba en `<repo>/config/`. Medido el 2026-09-25, las tres
consecuencias:

  1. `pip install -e ".[dev]"` resolvia `config/pyproject.toml`, que declaraba
     `build-backend = "setuptools.backends._legacy:_Backend"` -> modulo
     INEXISTENTE. El paso de install fallaba.
  2. `pytest tests/` con `testpaths=["tests"]` resolvia a `config/tests`, que NO
     EXISTE. Los tests no corrian nunca.
  3. `ruff check .` linteaba el contenido de config/ (JSON, Caddyfiles,
     Dockerfiles). La puerta de lint era vacua.

O sea: **la CI podia estar verde sin haber comprobado nada**. Ese es el fallo
que este script existe para impedir que vuelva.

Por que un script y no un heredoc dentro del YAML
-------------------------------------------------
Dos razones, la segunda medida:

  1. Se puede ejecutar en local: `python scripts/core/ci_precondiciones.py`.
  2. `tests/core/test_referencias_integridad.py::test_rutas_de_workflow_existen`
     lee el workflow y trata toda ruta entre comillas simples como ruta de
     fichero, usando el `working-directory` del workflow como base. Un heredoc
     con `"config/pyproject.toml"` dentro del YAML se interpretaba como
     `config/config/pyproject.toml` y ponia el test en rojo. Sacando la logica
     aqui, el YAML solo cita el script (que si existe).

Uso:
    python scripts/core/ci_precondiciones.py     # 0 = OK, 1 = abortar
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import tomllib

RAIZ = pathlib.Path.cwd()

# Los tres pyproject.toml del repo. Se construyen con `/` en vez de como
# literales con barra para que el checador de rutas del workflow no los vea.
PYPROJECTS = (
    RAIZ / "pyproject.toml",
    RAIZ / "config" / "pyproject.toml",
    RAIZ / "shared" / "pyproject.toml",
)


def _backend(pyproject: pathlib.Path) -> str:
    datos = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return datos["build-system"]["build-backend"]


def main() -> int:
    fallos: list[str] = []

    # 1. Todo build-backend declarado tiene que existir DE VERDAD.
    for p in PYPROJECTS:
        if not p.is_file():
            fallos.append(f"falta {p.relative_to(RAIZ).as_posix()}")
            continue
        backend = _backend(p)
        modulo = backend.split(":")[0]
        try:
            spec = importlib.util.find_spec(modulo)
        except (ImportError, ModuleNotFoundError, ValueError):
            spec = None
        if spec is None:
            fallos.append(
                f"{p.relative_to(RAIZ).as_posix()}: build-backend={backend!r} "
                f"no importable ({modulo!r})"
            )

    # 2. El cwd tiene que tener los tests. Si no, pytest no corre nada y la CI
    #    queda verde por vacio (fue el caso con working-directory: config).
    if not (RAIZ / "tests").is_dir():
        fallos.append(f"tests/ no existe en el cwd ({RAIZ})")

    # 3. La config de pytest tiene que ser la de la raiz, no la de config/.
    raiz_pyproject = RAIZ / "pyproject.toml"
    if raiz_pyproject.is_file():
        opciones = (
            tomllib.loads(raiz_pyproject.read_text(encoding="utf-8"))
            .get("tool", {})
            .get("pytest", {})
            .get("ini_options", {})
        )
        testpaths = opciones.get("testpaths")
        if testpaths != ["tests"]:
            fallos.append(f"testpaths de la raiz es {testpaths!r}, se esperaba ['tests']")

    if fallos:
        print("PRECONDICIONES INCUMPLIDAS:", file=sys.stderr)
        for f in fallos:
            print(f"  - {f}", file=sys.stderr)
        print(
            "\nAbortando: la CI no puede verificar nada si esto no se cumple. "
            "Revisa el `working-directory` del workflow.",
            file=sys.stderr,
        )
        return 1

    print("Precondiciones OK: backends importables, tests/ presente, testpaths=['tests'].")
    return 0


if __name__ == "__main__":
    sys.exit(main())

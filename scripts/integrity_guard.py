#!/usr/bin/env python3
"""Shim de conveniencia: la implementacion vive en agents/integrity_guard.py.

Ver docs/ARQUITECTURA.md — el repo usa un shim por modulo en scripts/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "aig" / "agents"))

from integrity_guard import (  # noqa: E402,F401
    MAX_FICHEROS,
    Alerta,
    Resultado,
    estado,
    hash_fichero,
    listar_ficheros,
    main,
    register_integrity_routes,
    sellar,
    verificar,
)

if __name__ == "__main__":
    sys.exit(main())

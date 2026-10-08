# daniela_os_core.py — shim hacia el cerebro de produccion.
"""NO usar este stub historico.

⚠️ Por que NO se llama `core.py`: `core/` esta en `sys.path` en produccion (lo
meten `daniela-os/server.py` y el Dockerfile), y un `core.py` AHI DENTRO gana
al paquete `core`: `import core` devuelve el shim y todo `from core.data...`
reventa con "'core' is not a package". Este nombre no lleva prefijo de marca y
no colisiona con nada.

Hasta 2026-09-18 este fichero devolvia ``Respuesta simulada...``.
El cerebro real vivia en ``/daniela_os_core.py`` (raiz del repo) y lo cargan
``daniela_os.get_core()`` y ``api_gateway`` por ruta explicita.

⚠️ 2026-09-20: el refactor ELIMINO ``/daniela_os_core.py`` de la raiz y dejo el
fichero en ``scripts/core/daniela_os_core.py`` (identico byte a byte al antiguo,
solo cambian los finales de linea). Este shim seguia apuntando a la ruta vieja,
asi que **reventaba con FileNotFoundError al importarlo** — y con el, todos los
tests que cargan el core por ruta.

Se aceptan las dos ubicaciones por orden de preferencia para no romper checkouts
antiguos ni scripts que aun copien el fichero a la raiz.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

# 2026-09-30 (Fase 2 del triage): el cerebro hace
# `from model_router import get_instance` (`scripts/core/daniela_os_core.py:175`)
# y ese modulo vive en `core/model_router.py`. En produccion lo mete en el path
# `scripts/daniela/daniela_os.py:147` y `gev/daniela-os/server.py` (el
# "resuelve por `core/`" del Dockerfile); en cambio un pytest suelto de
# `tests/agents/test_anti_stub.py` no trae `core/` y el import reventaba con
# ModuleNotFoundError. Se anade AL FINAL de `sys.path`: si se anadiera por
# delante, `core/server.py` pasaria a ganarle al `server.py` de
# `daniela-omnipresente/` en el choque de nombres que purga `tests/conftest.py`.
_CORE_DIR = str(_ROOT / "core")
if _CORE_DIR not in sys.path:
    sys.path.append(_CORE_DIR)

_CANDIDATAS = (
    _ROOT / "scripts" / "core" / "daniela_os_core.py",
    _ROOT / "daniela_os_core.py",
)

_CORE = next((c for c in _CANDIDATAS if c.is_file()), None)
if _CORE is None:
    raise ImportError(
        "no se encontro daniela_os_core.py. Rutas probadas:\n  "
        + "\n  ".join(str(c) for c in _CANDIDATAS)
    )

_spec = importlib.util.spec_from_file_location("daniela_os_core_prod_shim", _CORE)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"no se pudo cargar {_CORE}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

DanielaCore = _mod.DanielaCore
PipelineStep = _mod.PipelineStep
PipelineResult = _mod.PipelineResult
SinProveedorError = _mod.SinProveedorError
Module = getattr(_mod, "Module", None)
Registry = getattr(_mod, "Registry", None)

__all__ = [
    "DanielaCore",
    "PipelineStep",
    "PipelineResult",
    "SinProveedorError",
    "Module",
    "Registry",
]


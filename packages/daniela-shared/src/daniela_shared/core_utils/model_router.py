# model_router.py — shim fino hacia el enrutador canonico.
"""Resuelve `import model_router` por `core/` (patron de `scripts/model_router.py`).

La fuente de verdad NO vive aqui: es `mobile-app/core/autonomy/model_router.py`.
Este fichero existe solo porque hay codigo que hace `from model_router import
get_instance` **sin** haber insertado `mobile-app` en `sys.path`:

  * el cerebro (`scripts/core/daniela_os_core.py:175`, cargado por `core/daniela_os_core.py`)
  * `scripts/daniela/daniela_os.py` y `gev/daniela-os/server.py`, que meten
    `<raiz>/core` en `sys.path` — de ahi el "resuelve por `core/`" del
    comentario de `gev/daniela-os/Dockerfile`.

⚠️ Se carga POR RUTA (igual que `core/daniela_os_core.py`), no con
`from core.autonomy.model_router import *` como hace `scripts/model_router.py`:
en una misma sesion de pytest el paquete `core` (el de la raiz) ya esta en
`sys.modules` — lo mete `from core.server import app` en
`tests/daniela/test_daniela.py` — y entonces `core.autonomy` daria
ModuleNotFoundError. Cargar por ruta no depende de como se llame el paquete.

Candidatas, por orden:
  1. `mobile-app/core/autonomy/model_router.py` (canonico)
  2. `scripts/core/model_router.py` (la misma linea, movida ahi en e1dc1505)

Ninguna de las dos esta en la imagen de Daniela (`mobile-app` va en
`.dockerignore`; `scripts/core/` solo copia `daniela_os_core.py`): ahi el import
falla igual que fallaba antes con ModuleNotFoundError, pero con un mensaje que
dice que falta y donde mirar.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]
_CANDIDATAS = (
    _RAIZ / "frontend" / "apps" / "android-app" / "mobile-app" / "core" / "autonomy" / "model_router.py",
    _RAIZ / "mobile-app" / "core" / "autonomy" / "model_router.py",
    _RAIZ / "scripts" / "core" / "model_router.py",
)

_RUTA = next((c for c in _CANDIDATAS if c.is_file()), None)
if _RUTA is None:
    raise ImportError(
        "no se encontro el enrutador de modelos. Rutas probadas:\n  "
        + "\n  ".join(str(c) for c in _CANDIDATAS)
    )

_spec = importlib.util.spec_from_file_location("model_router_impl", _RUTA)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"no se pudo cargar {_RUTA}")
_impl = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _impl
_spec.loader.exec_module(_impl)

# Re-export explicito de lo que consumen el cerebro, `daniela_os` y los tests.
EnrutadorModelos = _impl.EnrutadorModelos
get_instance = _impl.get_instance
register_router_routes = _impl.register_router_routes

# El estado (singleton `_INSTANCIA`, `POR_ID`, `historial`…) vive en el modulo
# real: este shim no guarda copia, para que `model_router.X` siempre devuelva
# el valor vigente de la fuente.
def __getattr__(name: str):
    """PEP 562: cualquier otro simbolo se delega al enrutador real."""
    return getattr(_impl, name)


__all__ = ["EnrutadorModelos", "get_instance", "register_router_routes"]

"""
gev (capa de compatibilidad, 2026-10-03)
=========================================
El antiguo paquete `gev/` de la raiz se fusiono en `daniela-os/` (outer) durante
la mega-reestructura. En vez de renombrar las ~20 referencias `gev.*` del repo
(runtime, tests, docstrings), este paquete redirige la busqueda de submodulos:

    from gev.gev_server import register_gev_routes  # -> daniela-os/gev_server.py
    from gev import gev_proxy                     # -> daniela-os/gev_proxy.py
    from gev.memoria import registrar_memoria     # -> daniela-os/memoria.py

`__path__` apunta al directorio `daniela-os/`, asi que CUALQUIER
`gev.<modulo>` resuelve a `daniela-os/<modulo>.py` sin duplicar ficheros.
"""

from __future__ import annotations

from pathlib import Path as _Path

__path__ = [str(_Path(__file__).resolve().parent.parent / "daniela-os")]
__all__ = ["register_gev_routes"]


def register_gev_routes(app):
    """Atajo (mismo contracto viejo): importa y registra las rutas del visor."""
    # 2026-10-04 (P1): `daniela-os/server.py` es ahora la app principal; el
    # modulo del visor se renombro a `daniela-os/gev_server.py`.
    from .gev_server import register_gev_routes as _reg

    return _reg(app)

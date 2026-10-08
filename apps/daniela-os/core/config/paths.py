"""Re-export de las rutas canonicas del repo.

Este fichero **no implementa nada**: la copia canonica es
`core/config/paths.py` (en la raiz), que ademas trae las rutas de las bases de
datos SQLite. aqui quedaban duplicados `WEB_PORT`, `load_env` y `validate_env`
bajo el MISMO nombre punteado (`core.config.paths`), y como el paquete de la raiz
es regular (tiene `__init__.py`) y este es una porcion de namespace, el de la
raiz ganaba siempre: la suite pasaba o fallaba segun el orden de recoleccion.

Se conserva el modulo para no romper un import por ruta, sin segunda
implementacion. Ver `core/config/paths.py`.
"""

from core.config.paths import WEB_PORT, load_env, validate_env

__all__ = ["WEB_PORT", "load_env", "validate_env"]

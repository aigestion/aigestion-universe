"""Rutas canonicas de las bases de datos sueltas, para los modulos de `core/`.



POR QUE EXISTE

--------------

La fuente de verdad es `core/paths.py`. Pero los modulos de `core/` se

importan como TOP-LEVEL (`import auth_system`) porque `tests/conftest.py` mete

`core/` en `sys.path`; en ese contexto `from core.paths import ...`

depende de que la raiz del repo tambien este en el path, cosa que no siempre

ocurre (un script suelto dentro de `core/` no la tiene).



Este modulo concentra esa fragilidad en UN sitio, en vez de repetir un

`try/except ImportError` en cada consumidor.



QUE PROBLEMA RESUELVE

---------------------

Las bases se abrian con el nombre relativo ("aig_auth.db"), asi que SQLite

las creaba en el DIRECTORIO DE TRABAJO. Resultado medido el 2026-09-21: 8 `.db`

sueltos en la raiz del repo, casi todos VACIOS, mientras el dato bueno vivia en

`data/`. El caso mas caro, `memory_rag.db`: 16 KB con 0 filas en la raiz frente a

1,4 MB con 89 filas en `data/`.



Estas constantes son ABSOLUTAS a proposito: una ruta relativa se resuelve contra

el cwd y vuelve a crear el fichero vacio en la raiz.

"""



from __future__ import annotations

from pathlib import Path

try:  # Camino normal: la raiz del repo esta en sys.path.

    from paths import (
        AUTH_DB,
        BILLING_DB,
        DANIELA_DB,
        DANIELA_MULTIUSER_DB,
        DB_DIR,
        MEMORY_RAG_DB,
        SCHEDULER_LOCKS_DB,
        TRIGGER_WATCHES_DB,
        WHITELABEL_DB,
    )

except ImportError:  # compat: en 2026-09-29 `core/paths.py` se aplano a `paths.py`

    try:

        from core.paths import (
            AUTH_DB,
            BILLING_DB,
            DANIELA_DB,
            DANIELA_MULTIUSER_DB,
            DB_DIR,
            MEMORY_RAG_DB,
            SCHEDULER_LOCKS_DB,
            TRIGGER_WATCHES_DB,
            WHITELABEL_DB,
        )

    except ImportError:  # pragma: no cover - sin la raiz en sys.path

        import os



        # Raiz por marcador (igual que `paths._repo_root`): el fichero se

        # aplano de `core/` a la raiz y un `parents[N]` fijo se equivocaba.

        _aqui = Path(__file__).resolve()

        _raiz = next(

            (

                c

                for c in (_aqui.parent, *_aqui.parents)

                if (c / ".git").exists() or (c / "tests" / "conftest.py").exists()

            ),

            _aqui.parent,

        )

        DB_DIR = _raiz / "data"



        def _db(nombre: str, variable: str) -> Path:

            entorno = (os.getenv(variable) or "").strip()

            return Path(entorno).expanduser().resolve() if entorno else DB_DIR / nombre



        DANIELA_DB = _db("daniela.db", "DANIELA_DB")

        AUTH_DB = _db("auth.db", "DANIELA_AUTH_DB")

        BILLING_DB = _db("billing.db", "DANIELA_BILLING_DB")

        WHITELABEL_DB = _db("whitelabel.db", "DANIELA_WHITELABEL_DB")

        DANIELA_MULTIUSER_DB = _db("daniela_multiuser.db", "DANIELA_MULTIUSER_DB")

        SCHEDULER_LOCKS_DB = _db("scheduler_locks.db", "SCHEDULER_LOCKS_DB")

        TRIGGER_WATCHES_DB = _db("trigger_watches.db", "TRIGGER_WATCHES_DB")

        MEMORY_RAG_DB = _db("memory_rag.db", "MEMORY_RAG_DB")





def ruta(nombre: str) -> Path:

    """Ruta canonica de una base por nombre de fichero.



    Util para migrar codigo que todavia pasa el nombre suelto:

        sqlite3.connect(ruta("daniela_multiuser.db"))

    """

    return DB_DIR / nombre





__all__ = [

    "DANIELA_DB",

    "AUTH_DB",

    "BILLING_DB",

    "DANIELA_MULTIUSER_DB",

    "DB_DIR",

    "MEMORY_RAG_DB",

    "SCHEDULER_LOCKS_DB",

    "TRIGGER_WATCHES_DB",

    "WHITELABEL_DB",

    "ruta",

]




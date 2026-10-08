"""Chequeos de salud de subsistemas para `/health` y `/health/ready`.

⚠️ POR QUE EXISTE ESTE MODULO
-----------------------------
Antes del 2026-09-20, `GET /health` devolvia:

    {"gateway": "healthy", "core": "online" | "offline", "timestamp": ...}

Es decir: comprobaba UN booleano (si `get_core()` devolvia algo) y nada mas. Un
sistema con el disco lleno, la memoria saturada, la base de datos inaccesible o
Daniela caida reportaba exactamente lo mismo que uno sano: `"healthy"`.

El repo SI tenia capacidad de medir (Prometheus, Grafana, dashboards) pero los
monitores estaban dispersos en ~20 ficheros distintos y nadie sabia cual
consultar. Este modulo los unifica en un unico punto de verdad.

DISEÑO: CHEQUEOS AISLADOS QUE NUNCA LANZAN
------------------------------------------
Regla critica: **un health check no puede tumbar el endpoint que lo sirve**. Si
comprobar la base de datos lanza una excepcion, `/health` debe seguir
respondiendo y reportar ese subsistema como `degraded`, no devolver un 500.

Por eso cada chequeo va envuelto en `_safe_check()`, que captura cualquier
excepcion y la convierte en un resultado de error. Es el mismo principio del
`fail-closed` del hook de git, pero al reves: aqui queremos `fail-visible`.

COSTO
-----
Puro stdlib (`shutil`, `os`) para los chequeos de recursos. No consulta la red
ni servicios externos: si lo hiciera, `/health` tardaria y dejaria de ser util
para un load balancer. Los chequeos que requieren E/S son rapidos y acotados.
"""
from __future__ import annotations

import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Umbrales. Se eligen para avisar ANTES de que el sistema falle, no despues.
DISK_WARN_PCT = 85.0      # % de disco usado
DISK_CRIT_PCT = 95.0
MEM_WARN_PCT = 85.0       # % de memoria usada (solo si se puede leer)
MEM_CRIT_PCT = 95.0


def _estado(ok: bool, warn: bool = False) -> str:
    """Traduce un resultado booleano al vocabulario de estados.

    - `healthy`: todo bien.
    - `degraded`: funciona pero en zona de riesgo (no rompe el servicio).
    - `unhealthy`: no funciona.
    """
    if not ok:
        return "unhealthy"
    return "degraded" if warn else "healthy"


def _safe_check(nombre: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Ejecuta un chequeo capturando CUALQUIER excepcion.

    Un health check que propaga una excepcion convierte un problema parcial en
    una caida total del endpoint. Aqui la excepcion se reporta como resultado,
    nunca se propaga.
    """
    inicio = time.time()
    try:
        resultado = fn()
    except Exception as exc:  # noqa: BLE001 — deliberado: ver docstring
        resultado = {
            "status": "unhealthy",
            "error": f"{type(exc).__name__}: {exc}",
        }
    resultado.setdefault("status", "unknown")
    resultado["latency_ms"] = round((time.time() - inicio) * 1000, 2)
    resultado["name"] = nombre
    return resultado


# ── Chequeos concretos ───────────────────────────────────────────

def check_disk(path: str = "/") -> dict[str, Any]:
    """Espacio en disco. Un disco lleno rompe logs, BD y subida de ficheros."""
    uso = shutil.disk_usage(path)
    pct = (uso.used / uso.total) * 100 if uso.total else 0.0
    warn = pct >= DISK_WARN_PCT
    crit = pct >= DISK_CRIT_PCT
    return {
        "status": _estado(ok=not crit, warn=warn),
        "used_pct": round(pct, 1),
        "free_gb": round(uso.free / (1024 ** 3), 2),
        "total_gb": round(uso.total / (1024 ** 3), 2),
    }


def check_memory() -> dict[str, Any]:
    """Memoria disponible. Se degrada con elegancia si no hay psutil.

    Sin `psutil` no se puede leer la memoria en Windows sin llamar a la API del
    sistema. En vez de mentir con un "healthy" falso, se reporta `unknown`: un
    dato ausente es mejor que un dato incorrecto.
    """
    try:
        import psutil
    except ImportError:
        return {"status": "unknown", "detail": "psutil no instalado"}

    mem = psutil.virtual_memory()
    warn = mem.percent >= MEM_WARN_PCT
    crit = mem.percent >= MEM_CRIT_PCT
    return {
        "status": _estado(ok=not crit, warn=warn),
        "used_pct": round(mem.percent, 1),
        "available_gb": round(mem.available / (1024 ** 3), 2),
    }


def check_scheduler() -> dict[str, Any]:
    """Comprueba que el planificador de agentes pueda cargar agentes.

    Contexto real: el refactor del 2026-09-20 movio `server.py` un nivel mas
    abajo y el scheduler dejo de encontrar los agentes. `_get_agent()` devolvia
    None y 18 tests fallaban. Nadie lo habria notado en produccion hasta que un
    agente no respondiera.

    Este chequeo existe para que ese fallo sea VISIBLE en `/health`.
    """
    raiz = _raiz_repo()
    # P1 2026-10-04: `daniela-os/` aplanado en la raiz (antes `gev/daniela-os/`).
    candidatos = [
        raiz / "daniela-os" / "shared" / "scheduler.py",
        raiz / "daniela-os" / "server.py",
    ]
    existentes = [str(c) for c in candidatos if c.exists()]
    return {
        "status": "healthy" if existentes else "unhealthy",
        "scheduler_files": len(existentes),
        "detail": "scheduler localizado" if existentes else "no se encuentra el scheduler ni server.py",
    }


# Marcadores de la raiz que SI viajan dentro de la imagen Docker.
#
# `.git` no sirve: `.dockerignore` lo excluye y el Dockerfile no copia `tests/`,
# asi que dentro del contenedor no existe ninguno de los dos. Medido dentro de
# `aig-daniela` el 2026-09-22: sin estos marcadores `_raiz_repo()` caia al
# `return aqui.parent` y devolvia `/app/core` en vez de `/app`.
#
# `core/`, `agents/` y `gev/` se copian a `/app/` (Dockerfile:27-29), asi
# que la raiz los tiene tanto en el host como en la imagen. Comprobado que
# ninguna subcarpeta imita los tres a la vez.
_MARCADORES = ("core", "agents", "gev")


def _raiz_repo() -> Path:
    """Localiza la raiz del repo subiendo hasta encontrar un marcador conocido.

    ⚠️ Por que NO se usa `parents[N]` con un indice fijo:

    Este modulo vive en `core/`, asi que la raiz es `parents[1]`. Pero ese mismo
    archivo podria reubicarse (es exactamente lo que paso en el refactor del
    2026-09-20, y la causa de casi todos sus fallos). Un indice fijo se rompe en
    silencio: devuelve un directorio valido pero equivocado, y el chequeo reporta
    ficheros como ausentes cuando existen.

    Eso fue lo que ocurrio en la primera version de este modulo: con
    `parents[2]` apuntaba a `C:\\Users\\Alejandro` y reportaba `degraded` con
    `.gitignore` "ausente" mientras el fichero estaba justo delante.

    Buscar un marcador es inmune a la profundidad: funciona igual desde `core/`,
    desde `scripts/core/` o desde la raiz. Y tambien dentro del contenedor, donde
    el arbol no tiene `.git`.
    """
    from pathlib import Path

    aqui = Path(__file__).resolve()
    candidatos = (aqui.parent, *aqui.parents)

    # 1) Checkout de desarrollo (host, CI): `.git` es el marcador mas fuerte.
    for candidato in candidatos:
        if (candidato / ".git").exists() or (candidato / "tests" / "conftest.py").exists():
            return candidato

    # 2) Imagen Docker: sin `.git` ni `tests/`, valen carpetas que si se copian.
    for candidato in candidatos:
        if all((candidato / m).is_dir() for m in _MARCADORES):
            return candidato

    return aqui.parent  # ultimo recurso: no fallar por no encontrar la raiz


def check_working_tree() -> dict[str, Any]:
    """Comprueba que los ficheros criticos de configuracion siguen presentes.

    Regresion directa del incidente del refactor: `.gitignore` y
    `.devcontainer/` desaparecieron y nadie lo detecto hasta dias despues.

    ⚠️ Los tres ficheros que se miran son artefactos de DESARROLLO y
    `.dockerignore` los deja fuera de la imagen. Dentro de un contenedor
    faltarian siempre, y el chequeo seria un `degraded` permanente — justo el
    ruido que el resto del modulo evita. Si el arbol no tiene `.git` ni `tests/`
    (o sea: es una imagen desplegada) se devuelve `unknown`, que NO degrada el
    conjunto (ver `_SEVERIDAD`).
    """
    raiz = _raiz_repo()
    if not (raiz / ".git").exists() and not (raiz / "tests").is_dir():
        return {
            "status": "unknown",
            "reason": "arbol sin .git/ ni tests/ (imagen desplegada): "
                      "el chequeo solo aplica a un checkout de desarrollo",
            "checked": 0,
        }
    criticos = [".gitignore", "tests/conftest.py", "scripts/core/ci_health_gate.py"]
    ausentes = [c for c in criticos if not (raiz / c).exists()]
    return {
        "status": "healthy" if not ausentes else "degraded",
        "missing": ausentes,
        "checked": len(criticos),
    }


# ── Agregacion ───────────────────────────────────────────────────

# Orden estable: el resultado de /health no debe cambiar entre llamadas.
_CHECKS: tuple = (
    ("disk", check_disk),
    ("memory", check_memory),
    ("scheduler", check_scheduler),
    ("config", check_working_tree),
)

# Severidad para agregar. `unknown` NO degrada el conjunto: no saber algo no es
# lo mismo que saber que algo va mal.
#
# Detalle que importa: `unknown` tiene la MISMA severidad que `healthy` (0).
# Si tuviera una mayor, un sistema sano pero sin `psutil` instalado reportaria
# `unknown` de forma permanente, y la senal perderia todo su valor: nadie mira
# un indicador que siempre esta en amarillo.
#
# Si en el futuro se quiere distinguir "no puedo medir" de "esta bien", la via
# correcta es anadir una clave aparte (`coverage`), no ensuciar `status`.
_SEVERIDAD = {"healthy": 0, "unknown": 0, "degraded": 2, "unhealthy": 3}


def run_all_checks() -> dict[str, Any]:
    """Ejecuta todos los chequeos y agrega el estado global.

    Devuelve un dict listo para serializar como JSON. La clave `status` global
    es el PEOR estado de los subsistemas, para que un load balancer pueda
    decidir con un solo campo.

    El desempate es DETERMINISTA: si dos subsistemas tienen la misma severidad
    (por ejemplo `healthy` y `unknown`, ambos 0), no se deja al azar cual gana.
    Se prefiere `healthy`, porque `unknown` solo aporta informacion cuando es
    peor que el resto. Sin este desempate, `max()` devolveria el primero de la
    lista y el resultado dependeria del orden de `_CHECKS`.
    """
    resultados = {}
    for nombre, fn in _CHECKS:
        resultados[nombre] = _safe_check(nombre, fn)

    estados = [r.get("status", "unknown") for r in resultados.values()]
    if not estados:
        return {"status": "unknown", "checks": {}, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S")}

    # El peor por severidad; a igual severidad, `healthy` gana el empate.
    severidad_max = max(_SEVERIDAD.get(s, 0) for s in estados)
    candidatos = [s for s in estados if _SEVERIDAD.get(s, 0) == severidad_max]
    peor = "healthy" if "healthy" in candidatos else candidatos[0]
    if severidad_max == 0 and "healthy" not in estados:
        peor = "unknown"

    return {
        "status": peor,
        "checks": resultados,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

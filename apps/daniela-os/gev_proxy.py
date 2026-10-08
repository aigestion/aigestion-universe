#!/usr/bin/env python3
"""
gev.gev_proxy — el God's Eye View completo dentro de Daniela
===========================================================================
El proyecto original (`bilawalsidhu/gev`) tiene 21 capas registradas
(18 visibles en su panel), 7 estilos visuales, HUD, cockpit, CCTV con
calibracion, radio, escenas, voz... Mucho mas que el visor propio.

No se puede reimplementar sin perder fidelidad, y **no se puede servir como
estatico**:

  1. Sus 22 proveedores de `/api/*` son middleware del servidor de desarrollo de
     Vite (`server/providers/local.js`). Un `vite build` estatico los pierde:
     tendrias el globo pero sin datos en vivo.
  2. Su servidor pone `X-Frame-Options: DENY` y `frame-ancestors 'none'`
     (`build/vite.js`), asi que no se puede meter en un iframe.

Por eso aqui se **lanza su servidor como servicio** y se expone bajo el mismo
origen de Daniela con un proxy inverso. El usuario navega a `/gods-eye/pro/` y
ve la aplicacion original, con todas sus funciones, sin iframe y sin segundo
origen.

Como se evita el choque de rutas
--------------------------------
La app se monta con `--base=/gods-eye/pro/`, de modo que Vite reescribe todas
sus rutas de assets y su `import.meta.env.BASE_URL` pasa a ser `/gods-eye/pro/`
(las partes de la app que ya respetan `BASE_URL` quedan correctas).

Sus llamadas a `/api/*` son absolutas y siguen yendo a la raiz, asi que se
proxean aparte. Se registran **reglas explicitas por prefijo**, no un catch-all,
para que no haya ninguna duda de precedencia con nuestras rutas
(`/api/globe/*`, `/api/cc/*`, `/api/billing/*`, `/api/i18n`): ninguno de los 28
prefijos del original coincide con los nuestros.

Honestidad si falta algo
------------------------
En la imagen Docker solo hay Python: no hay Node. En ese caso el modulo **no
falla**: declara `disponible: false` con el motivo y la ruta responde 503
explicando que falta, en vez de fingir que el visor completo esta ahi.

Uso:
  python -m gev.gev_proxy estado
  python -m gev.gev_proxy arrancar
  python -m gev.gev_proxy parar
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

_DIR = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.abspath(os.path.join(_DIR, os.pardir))
_CORE = os.path.join(_RAIZ, "core")
# Igual que `server.py`: la raiz y `core/`, pero NO `gev/` (ensucia el
# `sys.path[0]` y hace que `gev/i18n.py` pise a `ux_engine/i18n.py`).
# `gev/` solo en modo script, sin paquete.
for _p in (_RAIZ, _CORE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
if not __package__ and _DIR not in sys.path:
    sys.path.insert(0, _DIR)


def _importar_core(nombre: str) -> Any:
    """Importa un modulo de `aig/core` como parte del paquete.

    Mismo criterio que `server.py`: se prefiere `core.X` para no
    cargar una segunda copia del modulo, con respaldo al import suelto para que
    el visor siga funcionando en modo autonomo.
    """
    try:
        return importlib.import_module(f"core.{nombre}")
    except ModuleNotFoundError as e:
        if (e.name or "").split(".")[0] != "aig":
            raise
        return importlib.import_module(nombre)


# ── Configuracion ────────────────────────────────────────────

BASE_URL = "/gods-eye/pro"  # donde se monta la app original
RAIZ_REPO = Path(__file__).resolve().parents[1]

# Prefijos de `/api/*` que sirve el servidor del original. Lista cerrada a
# proposito: si manana el original anade uno, hay que anadirlo aqui, y asi
# nunca se proxea por accidente una ruta nuestra o desconocida.
PREFIJOS_API: tuple[str, ...] = (
    "adsbdb",
    "adsblol",
    "ais-live",
    "cctv",
    "celestrak",
    "firms",
    "gbfs",
    "geocode",
    "google",
    "launches",
    "military-installations",
    "openai",
    "opensky",
    "opensky-track",
    "overpass",
    "radio",
    "realtime",
    "regional-brief",
    "route",
    "setup",
    "terrain",
    "tomtom",
    "transit",
    "weather-effects",
)

# Node del original: engines >=24.14 <25 || >=26 <27. El Node gestionado de este
# entorno es 22.x y NO sirve; el del sistema (24.15) si.
NODE_MINIMO = (24, 14)

# Cabeceras hop-by-hop: no se reenvian (RFC 7230 6.1).
_CABECERAS_SALTADAS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    # El cuerpo lo reencoda Flask: longitudes y codificaciones viejas sobran.
    "content-length",
    "content-encoding",
}

_PROC: subprocess.Popen | None = None

# `arrancar()` se llama desde varios sitios a la vez: el precalentamiento en
# segundo plano del arranque y la primera peticion del usuario. Sin candado,
# los dos veian el puerto libre, los dos lanzaban Node, `--strictPort` hacia que
# uno muriera... y `_PROC` acababa apuntando al que murio, con lo que `parar()`
# decia "no hay sidecar" mientras el servidor seguia vivo y sin dueño.
_CANDADO = threading.Lock()


# ── Localizacion del original y de Node ──────────────────────


def raiz_original() -> Path | None:
    """Directorio del proyecto God's Eye View original, si esta disponible."""
    entorno = (os.getenv("DANIELA_GEV_DIR") or "").strip()
    candidatos: list[Path] = []
    if entorno:
        candidatos.append(Path(entorno))
    # Junto al repo (caso original), dentro del repo (donde vive HOY el
    # proyecto: `gev/daniela-os/` es el God's Eye View real, con `package.json`
    # e `index.html`) y en el despliegue.
    candidatos += [
        RAIZ_REPO / "gev" / "daniela-os",
        RAIZ_REPO.parent / "gev",
        RAIZ_REPO / "gev",
        RAIZ_REPO / "vendor" / "gev",
        Path("/opt/gev"),
    ]
    for c in candidatos:
        try:
            if (c / "package.json").is_file() and (c / "index.html").is_file():
                return c.resolve()
        except OSError:
            continue
    return None


def binario_node() -> str | None:
    """Node que cumple el `engines` del original, si lo hay."""
    candidatos: list[str] = []
    entorno = (os.getenv("DANIELA_NODE") or "").strip()
    if entorno:
        candidatos.append(entorno)
    cual = shutil.which("node")
    if cual:
        candidatos.append(cual)
    candidatos += [
        r"C:\Program Files\nodejs\node.exe",
        "/usr/local/bin/node",
        "/usr/bin/node",
    ]
    for c in candidatos:
        if not c or not os.path.exists(c):
            continue
        try:
            salida = subprocess.run(
                [c, "--version"], capture_output=True, text=True, timeout=10
            ).stdout.strip()
        except Exception:  # noqa: BLE001
            continue
        if _version_ok(salida):
            return c
    return None


def _version_ok(texto: str) -> bool:
    """True si `vMAJOR.MINOR.x` cumple el rango del original.

    El original declara: >=24.14.0 <25 || >=26 <27. Es decir, excluye 25.x.
    """
    t = (texto or "").strip().lstrip("v")
    try:
        mayor, menor = (int(x) for x in t.split(".")[:2])
    except (TypeError, ValueError):
        return False
    if mayor == 25:
        return False
    return (mayor, menor) >= NODE_MINIMO


def puerto() -> int:
    try:
        return int(os.getenv("DANIELA_GEV_PORT", "4173"))
    except (TypeError, ValueError):
        return 4173


def url_interna() -> str:
    """URL del servidor del original.

    `DANIELA_GEV_URL` permite apuntar a un servidor **externo** (por ejemplo el
    servicio `gods-eye` de docker-compose): en ese caso Daniela no lanza nada,
    solo proxea. Es la via recomendada en contenedor, porque evita meter Node y
    380 MB de proyecto en la imagen de Python.
    """
    externo = (os.getenv("DANIELA_GEV_URL") or "").strip().rstrip("/")
    return externo or f"http://127.0.0.1:{puerto()}"


def externo() -> bool:
    """True si el servidor del original lo gestiona otro (no lo lanzamos)."""
    return bool((os.getenv("DANIELA_GEV_URL") or "").strip())


def modo() -> str:
    """`dev` (por defecto) o `preview`.

    - `dev`: el servidor de desarrollo del original. Es como lo arranca su
      propio lanzador y es lo **unico** que trae el dialogo "Power up the globe"
      (su `key-setup.js` se instala a proposito solo con `configureServer`).
    - `preview`: sirve el build estatico (`dist/`) con los mismos proveedores.
      Mas ligero, pero **sin** el dialogo de claves. Medido: `/api/opensky`
      devuelve datos reales en los dos modos.
    """
    m = (os.getenv("DANIELA_GEV_MODO") or "dev").strip().lower()
    return m if m in ("dev", "preview") else "dev"


def _ocupado(host: str = "127.0.0.1", p: int | None = None) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, p or puerto())) == 0


def _sirve_base(timeout: float = 4.0) -> bool:
    """True si el puerto no solo esta abierto, sino que sirve NUESTRA base.

    Comprobar unicamente el puerto enganya: en este equipo quedo antes un Vite
    arrancado con `--base=/gods-eye/` (sin `/pro`) y el puerto respondia igual,
    asi que `arrancar()` habria dado por bueno un servidor que no sirve el
    visor donde toca.
    """
    import urllib.request

    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with op.open(f"{url_interna()}{BASE_URL}/", timeout=timeout) as r:
            return int(r.status) == 200
    except Exception:  # noqa: BLE001
        return False


def _ruta_log() -> Path:
    d = RAIZ_REPO / "aig" / "data" / "gev"
    d.mkdir(parents=True, exist_ok=True)
    return d / "gev_sidecar.log"


# ── Ciclo de vida del servicio ───────────────────────────────


def disponible() -> tuple[bool, str]:
    """(se puede usar el visor completo, motivo si no).

    En modo externo (`DANIELA_GEV_URL`) no hace falta Node ni el proyecto en
    local: solo que el servidor de enfrente responda.
    """
    if externo():
        if _sirve_base():
            return True, ""
        return False, (f"el servidor externo {url_interna()} no responde en {BASE_URL}/")

    raiz = raiz_original()
    if raiz is None:
        return False, (
            "no encuentro el proyecto God's Eye View original; "
            "define DANIELA_GEV_DIR o DANIELA_GEV_URL"
        )
    if not (raiz / "node_modules" / "vite").is_dir():
        return False, (
            f"falta node_modules en {raiz}; ejecuta `npm install` dentro del proyecto original"
        )
    if binario_node() is None:
        return False, (
            f"no hay Node >={NODE_MINIMO[0]}.{NODE_MINIMO[1]} <25 "
            "(la imagen solo-Python no lo trae); el visor completo "
            "necesita Node, o define DANIELA_GEV_URL apuntando a un "
            "servicio aparte"
        )
    if modo() == "preview" and not (raiz / "dist" / "index.html").is_file():
        return False, (f"modo preview pero no hay build en {raiz}/dist; ejecuta `npm run build`")
    return True, ""


def arrancar(espera: float = 25.0) -> dict[str, Any]:
    """Lanza el servidor del original si no esta ya escuchando.

    Serializado con `_CANDADO`: dos llamadas simultaneas (precalentamiento +
    primera visita) no deben lanzar dos servidores.
    """
    with _CANDADO:
        return _arrancar_sin_candado(espera)


def _arrancar_sin_candado(espera: float) -> dict[str, Any]:
    global _PROC
    ok, motivo = disponible()
    if not ok:
        return {"ok": False, "motivo": motivo}

    if _sirve_base():
        # Ya hay alguien sirviendo nuestra base. Si no es hijo nuestro, es un
        # servidor externo: se dice, no se finge que lo gestionamos.
        nuestro = _PROC is not None and _PROC.poll() is None
        return {
            "ok": True,
            "ya_estaba": True,
            "gestionado": nuestro,
            "externo": externo(),
            "url": f"{url_interna()}{BASE_URL}/",
        }

    if externo():
        # Lo gestiona otro (p. ej. un servicio de docker-compose). No lanzamos
        # nada: esperamos a que responda, y si no, se dice.
        limite = time.time() + espera
        while time.time() < limite:
            if _sirve_base():
                return {"ok": True, "externo": True, "url": f"{url_interna()}{BASE_URL}/"}
            time.sleep(0.5)
        return {
            "ok": False,
            "motivo": (
                f"el servidor externo {url_interna()} no responde en {BASE_URL}/ tras {espera:.0f}s"
            ),
        }

    if _ocupado():
        return {
            "ok": False,
            "motivo": (
                f"el puerto {puerto()} esta ocupado por otro proceso que no sirve "
                f"{BASE_URL}/; libéralo o cambia DANIELA_GEV_PORT"
            ),
        }

    raiz = raiz_original()
    assert raiz is not None
    node = binario_node()
    assert node is not None

    entorno = dict(os.environ)
    entorno.update(
        {
            "PORT": str(puerto()),
            "HOST": "127.0.0.1",
            # Sin esto, requests/urllib dentro del propio Node no deberian verse
            # afectados, pero dejamos constancia de que el sidecar es local.
            "NODE_ENV": entorno.get("NODE_ENV", "development"),
        }
    )
    # El proxy de entorno de esta maquina rompe las llamadas a localhost.
    for clave in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        entorno.pop(clave, None)
    entorno["NO_PROXY"] = "127.0.0.1,localhost"
    entorno["no_proxy"] = "127.0.0.1,localhost"

    log = open(_ruta_log(), "a", encoding="utf-8", errors="replace")
    log.write(
        f"\n=== arranque {time.strftime('%Y-%m-%d %H:%M:%S')} "
        f"modo={modo()} node={node} base={BASE_URL}/ ===\n"
    )
    log.flush()

    # `dev` sirve el codigo fuente y trae el dialogo de claves ("Power up the
    # globe"). `preview` sirve el build de `dist/` con los MISMOS proveedores
    # (medido: /api/opensky da datos reales), pero sin ese dialogo.
    if modo() == "preview":
        comando = [
            node,
            "node_modules/vite/bin/vite.js",
            "preview",
            f"--base={BASE_URL}/",
            "--port",
            str(puerto()),
            "--host",
            "127.0.0.1",
            "--strictPort",
        ]
    else:
        comando = [node, "node_modules/vite/bin/vite.js", f"--base={BASE_URL}/", "--strictPort"]

    # El sidecar debe SOBREVIVIR a quien lo lanza: si no, al terminar el
    # proceso que lo arranco (CLI, recarga del servidor, gestor de procesos que
    # mata su grupo) el visor completo se caeria solo. Se desacopla del grupo.
    sueltas = 0
    if os.name == "nt":
        sueltas = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
            subprocess, "DETACHED_PROCESS", 0
        )
    try:
        _PROC = subprocess.Popen(
            comando,
            cwd=str(raiz),
            env=entorno,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=sueltas,
            **({} if os.name == "nt" else {"start_new_session": True}),
        )
    except OSError as e:
        return {"ok": False, "motivo": f"no se pudo lanzar Node: {e}"}

    limite = time.time() + espera
    while time.time() < limite:
        if _sirve_base():
            return {
                "ok": True,
                "arrancado": True,
                "pid": _PROC.pid,
                "url": f"{url_interna()}{BASE_URL}/",
            }
        if _PROC.poll() is not None:
            return {
                "ok": False,
                "motivo": (
                    f"el servidor del original murio al arrancar (codigo "
                    f"{_PROC.returncode}); revisa {_ruta_log()}"
                ),
            }
        time.sleep(0.5)
    return {
        "ok": False,
        "motivo": (f"el servidor del original no respondio en {espera:.0f}s; revisa {_ruta_log()}"),
    }


def parar() -> dict[str, Any]:
    """Detiene el sidecar si lo lanzamos nosotros."""
    with _CANDADO:
        return _parar_sin_candado()


def _parar_sin_candado() -> dict[str, Any]:
    global _PROC
    if _PROC is None or _PROC.poll() is not None:
        _PROC = None
        if _sirve_base():
            return {
                "ok": False,
                "parado": False,
                "motivo": (
                    "el servidor responde pero no lo lanzo este proceso: lo para "
                    "quien lo arranco (o el gestor de procesos), no Daniela"
                ),
            }
        return {"ok": True, "parado": False, "motivo": "no hay sidecar lanzado por este proceso"}
    _PROC.terminate()
    try:
        _PROC.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _PROC.kill()
        _PROC.wait(timeout=5)
    _PROC = None
    return {"ok": True, "parado": True}


def precalentar() -> bool:
    """Arranca el sidecar en segundo plano para que la primera visita no espere.

    No bloquea: Vite tarda ~2-5 s en estar listo y no queremos retrasar el
    arranque de Daniela por un visor que quizas nadie abra en esta sesion. Si
    aun asi el usuario llega antes de que termine, `_reenviar` arranca o espera
    lo que haga falta.
    """
    ok, _motivo = disponible()
    if not ok or _sirve_base() or externo():
        # En modo externo no hay nada que precalentar: el ciclo de vida de ese
        # servidor no es nuestro.
        return False

    def _tarea() -> None:
        try:
            arrancar(espera=45.0)
        except Exception:  # noqa: BLE001
            pass

    threading.Thread(target=_tarea, name="gev-precalentar", daemon=True).start()
    return True


def estado() -> dict[str, Any]:
    """Estado real del visor completo, sin adornos."""
    raiz = raiz_original()
    ok, motivo = disponible()
    vivo = _sirve_base()
    d: dict[str, Any] = {
        "ok": True,
        "base": f"{BASE_URL}/",
        "puerto": puerto(),
        "url": url_interna(),
        "externo": externo(),
        "modo": modo(),
        "servidor_vivo": vivo,
        "puerto_ocupado": _ocupado(),
        "disponible": ok,
        "nodo": binario_node(),
        "raiz": str(raiz) if raiz else None,
        "gestionado": _PROC is not None and _PROC.poll() is None,
        "capas_api": len(PREFIJOS_API),
    }
    if not ok:
        d["motivo"] = motivo
    if raiz is not None:
        d["log"] = str(_ruta_log())
    return d


# ── Proxy inverso ────────────────────────────────────────────


def _reenviar(destino: str):
    """Reenvia la peticion actual al servidor del original."""
    from flask import Response, request

    try:
        import requests
    except ImportError as e:
        return _json({"ok": False, "error": f"falta requests: {e}"}, 503)

    if not _ocupado():
        # Intento perezoso de arranque: el usuario abrio el visor y el servicio
        # no estaba. Mejor arrancarlo que devolver un error opaco.
        arranque = arrancar(espera=20.0)
        if not arranque.get("ok"):
            return _json(
                {
                    "ok": False,
                    "error": "el visor completo no esta disponible",
                    "motivo": arranque.get("motivo"),
                },
                503,
            )

    consulta = request.query_string.decode("utf-8", "replace")
    url = f"{url_interna()}{destino}" + (f"?{consulta}" if consulta else "")
    cabeceras = {k: v for k, v in request.headers.items() if k.lower() not in _CABECERAS_SALTADAS}
    # El original es local-only: mentimos lo justo para que su `allowedHosts`
    # no rechace la peticion reenviada.
    cabeceras["Host"] = f"127.0.0.1:{puerto()}"

    try:
        r = requests.request(
            method=request.method,
            url=url,
            headers=cabeceras,
            data=request.get_data(),
            stream=True,
            timeout=(10, 120),
            allow_redirects=False,
            # Clave: `requests` respeta HTTP_PROXY del entorno, y en esta
            # maquina hay uno que responde 502 a localhost.
            proxies={"http": None, "https": None},
        )
    except Exception as e:  # noqa: BLE001
        return _json(
            {"ok": False, "error": f"el visor completo no responde: {type(e).__name__}: {e}"}, 502
        )

    salida = {k: v for k, v in r.headers.items() if k.lower() not in _CABECERAS_SALTADAS}
    return Response(
        r.iter_content(chunk_size=16384),
        status=r.status_code,
        headers=salida,
        direct_passthrough=True,
    )


def _json(d: dict[str, Any], codigo: int = 200):
    from flask import Response

    return Response(json.dumps(d, ensure_ascii=False), status=codigo, mimetype="application/json")


def _autorizado() -> tuple[bool, Any]:
    """Admin o cliente identificado. Sin sujeto, no se sirve el visor."""
    try:
        acc = _importar_core("access")
    except Exception:  # noqa: BLE001
        return True, None  # sin control de acceso, no bloqueamos
    from flask import request

    s = acc.sujeto_desde_request(request)
    if s.es_admin or s.tenant_slug:
        return True, s
    return False, s


def registrar_gev_proxy(app) -> None:
    """Monta el visor completo y sus APIs bajo el mismo origen de Daniela."""
    metodos = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

    @app.route(f"{BASE_URL}/", methods=metodos, defaults={"resto": ""})
    @app.route(f"{BASE_URL}/<path:resto>", methods=metodos)
    def gev_pro_completo(resto: str):
        permitido, _s = _autorizado()
        if not permitido:
            return _json(
                {
                    "ok": False,
                    "error": "acceso denegado",
                    "detalle": "se requiere admin o tenant identificado",
                },
                403,
            )
        return _reenviar(f"{BASE_URL}/{resto}")

    # Sin barra final, la app se rompe (sus rutas relativas se resuelven mal).
    @app.route(BASE_URL)
    def gev_pro_sin_barra():
        from flask import redirect

        return redirect(f"{BASE_URL}/", code=308)

    # APIs del original, reglas explicitas por prefijo (sin catch-all).
    for prefijo in PREFIJOS_API:

        def _vista(resto: str = "", _p: str = prefijo):
            permitido, _s = _autorizado()
            if not permitido:
                return _json({"ok": False, "error": "acceso denegado"}, 403)
            cola = f"/{resto}" if resto else ""
            return _reenviar(f"/api/{_p}{cola}")

        app.add_url_rule(
            f"/api/{prefijo}", endpoint=f"gev_api_{prefijo}", view_func=_vista, methods=metodos
        )
        app.add_url_rule(
            f"/api/{prefijo}/<path:resto>",
            endpoint=f"gev_api_{prefijo}_sub",
            view_func=_vista,
            methods=metodos,
        )

    # -- gestion del servicio (solo admin) --

    @app.route("/api/gev/estado")
    def gev_estado():
        return _json(estado())

    @app.route("/api/gev/arrancar", methods=["POST"])
    def gev_arrancar():
        permitido, s = _autorizado()
        if not permitido or not getattr(s, "es_admin", False):
            return _json(
                {"ok": False, "error": "solo el administrador puede arrancar el visor completo"},
                403,
            )
        resultado = arrancar()
        return _json(resultado, 200 if resultado.get("ok") else 503)

    @app.route("/api/gev/parar", methods=["POST"])
    def gev_parar():
        permitido, s = _autorizado()
        if not permitido or not getattr(s, "es_admin", False):
            return _json({"ok": False, "error": "solo el administrador"}, 403)
        return _json(parar())

    e = estado()
    print(
        f"[God's Eye Pro] visor completo en {BASE_URL}/ "
        f"({'listo' if e['servidor_vivo'] else 'servicio parado'}; "
        f"{'arrancable' if e['disponible'] else e.get('motivo', 'no disponible')})"
    )


# ── CLI ──────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    orden = args[0] if args else "estado"
    if orden == "estado":
        print(json.dumps(estado(), indent=2, ensure_ascii=False))
        return 0
    if orden == "arrancar":
        print(json.dumps(arrancar(), indent=2, ensure_ascii=False))
        return 0
    if orden == "parar":
        print(json.dumps(parar(), indent=2, ensure_ascii=False))
        return 0
    print("uso: gev_proxy.py [estado|arrancar|parar]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(_main())

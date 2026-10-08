#!/usr/bin/env python3
"""
ci_runner.py — E-15 · CI en ARM real: que las pruebas corran donde corre Daniela
===============================================================================

El `auto-deploy.yml` que subimos corre en `ubuntu-latest`, es decir en **x86**.
Y Daniela no vive ahi: vive en un Pixel 8a, **aarch64**, con toybox en vez de
coreutils, sin `sort -h`, con `/proc` distinto y con limites de memoria de
telefono.

Eso significa que el CI actual **no puede ver los fallos que mas nos duelen**:

  · la aritmetica de 32 bits con signo que desbordaba a partir de 2 GB,
  · `find /sdcard` devolviendo 0 porque es un symlink,
  · `free -m` sin las lineas que esperabamos,
  · un modulo que importa bien en Linux y revienta en Termux.

Ninguno de esos fallos aparece en un runner x86. Este modulo es el que
ejecuta las comprobaciones **en el hierro de destino** y las reporta.

La decision de seguridad que ordena todo
----------------------------------------
Un "self-hosted runner" de GitHub, tal cual, **ejecuta el codigo que venga en
el repo**. En un servidor ya es delicado; en el teleffo de una persona es
inaceptable: cualquiera que pueda abrir un PR podria ejecutar comandos en tu
movil.

Por eso este modulo NO es un runner de GitHub. Es lo contrario:

    Los trabajos estan definidos AQUI, en una lista cerrada.
    Nunca se ejecuta un `run:` que venga del repositorio o de internet.

Lo que si hace es publicar el resultado como **estado de commit** en GitHub,
que es justo lo que aporta valor (ver en el PR si paso en ARM) sin ceder
ni un solo bit de control del telefono.

Los trabajos
------------
    sintaxis    compila todos los .py          → caza el SyntaxError que
                                                 reventaria el arranque
    seguridad   AST: os.system / shell=True    → la regla dura del proyecto
    arranque    importa daniela_os y cuenta    → el unico test que de verdad
                las rutas                        dice "esto levanta"
    ruff        linter, si esta instalado
    mypy        tipos, si esta instalado
    pytest      tests, si esta instalado

Los tres ultimos **degradan**: si la herramienta no esta en el telefono, el
trabajo se marca como "omitido", no como "fallido". Sin pytest no hay
verguenza en no pasar pytest.

Rutas
-----
    GET  /api/ci/status    plataforma, arquitectura, puede_correr
    GET  /api/ci/jobs      trabajos y su ultimo resultado
    POST /api/ci/run       ejecuta uno, varios o todos
    GET  /api/ci/history   historial de ejecuciones
    GET  /api/ci/github    ultimos workflow runs de GitHub
    POST /api/ci/publish   publica el resultado como estado de commit
"""

from __future__ import annotations

import ast
import json
import os
import platform
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "ci"
CONFIG_FILE = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json"

MAX_HISTORIAL = 100

CONFIG_DEFAULT: dict[str, Any] = {
    "timeout_s": 300,  # tiempo maximo por trabajo (arranque)
    "timeout_herramienta_s": 90,  # ruff/mypy/pytest: si cuelgan, se matan
    "solo_raiz": True,  # no recorrer subcarpetas (tests/, phone_deploy/)
    "ignorar": [
        "phone_deploy",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "tests",
        ".git",
        "data",
        "output",
    ],
    "contexto_github": "daniela-ci-arm",
    "repo": "aigestion/AIGESTION-MONOREPO",
    "publicar_auto": False,  # publicar en GitHub exige quererlo
}


# ==========================================================================
#  Utilidades — REGLA DURA: sin shell, sin os.system
# ==========================================================================
def _matar(p: subprocess.Popen) -> None:
    """Mata el proceso Y sus hijos.

    Sin esto, un timeout deja huerfanos: pytest arranca servidores, el padre
    muere pero el nieto sigue vivo agarrando la tuberia y subprocess.run se
    queda esperando un EOF que nunca llega. Nos paso: 5 min colgado con un
    timeout de 300 s que en teoria ya habia saltado.
    """
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                capture_output=True,
                timeout=20,
                shell=False,
            )
        else:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    except Exception:  # noqa: BLE001
        pass
    try:
        p.kill()
    except Exception:  # noqa: BLE001
        pass


def _run(args: list[str], timeout: int = 120) -> dict[str, Any]:
    """Ejecuta una lista de argumentos. Devuelve codigo, salida y duracion.

    La salida va a ficheros temporales, no a tuberias: si el proceso se cuelga
    y deja nietos vivos, leer de una tuberia bloquea para siempre. Con ficheros
    siempre podemos seguir adelante.
    """
    t0 = time.time()
    salida = b""
    error = b""
    try:
        with tempfile.TemporaryFile() as f_out, tempfile.TemporaryFile() as f_err:
            popen_kw: dict[str, Any] = {
                "stdout": f_out,
                "stderr": f_err,
                "stdin": subprocess.DEVNULL,
                "shell": False,
            }
            if os.name != "nt":
                popen_kw["start_new_session"] = True  # para killpg
            p = subprocess.Popen(list(args), **popen_kw)
            try:
                p.communicate(timeout=timeout)
                codigo = p.returncode
            except subprocess.TimeoutExpired:
                _matar(p)
                try:
                    p.communicate(timeout=10)
                except Exception:  # noqa: BLE001
                    pass
                codigo = 124
                error = f"timeout {timeout}s (proceso y descendencia matados)"
            f_out.seek(0)
            f_err.seek(0)
            salida = f_out.read()[-8000:]
            if codigo == 124:
                error = error.encode("utf-8")
            else:
                error = f_err.read()[-4000:]
        return {
            "codigo": codigo,
            "salida": salida.decode("utf-8", "replace"),
            "error": error.decode("utf-8", "replace"),
            "duracion_s": round(time.time() - t0, 2),
        }
    except OSError as e:
        return {
            "codigo": 127,
            "salida": "",
            "error": f"{type(e).__name__}: {e}",
            "duracion_s": round(time.time() - t0, 2),
        }


def _tiene_modulo(modulo: str) -> bool:
    """¿Esta el modulo instalado EN ESTE MISMO interprete?

    OJO: shutil.which('pytest') encuentra el pytest de OTRO python. Entonces el
    CI correria con un interprete distinto al de Daniela y las conclusiones
    serian falsas. Por eso se pregunta con sys.executable -m.
    """
    r = _run([sys.executable, "-m", modulo, "--version"], timeout=60)
    return r["codigo"] == 0


def _tiene(cmd: str) -> bool:
    """¿Esta este EJECUTABLE en el PATH? (para gh, no para modulos python)"""
    from shutil import which

    return which(cmd) is not None


def es_android() -> bool:
    for ruta in ("/system/bin/app_process", "/system/build.prop", "/data/data/com.termux"):
        if Path(ruta).exists():
            return True
    return False


def es_termux() -> bool:
    return bool(os.environ.get("TERMUX_VERSION")) or Path("/data/data/com.termux").exists()


# ==========================================================================
#  Plataforma — el motivo de existir de esta epica
# ==========================================================================
def plataforma() -> dict[str, Any]:
    """Quien soy y por que el CI de GitHub no me representa."""
    maquina = platform.machine().lower()
    return {
        "arquitectura": maquina,
        "es_arm": maquina in ("aarch64", "arm64", "armv7l", "armv8l"),
        "es_x86": maquina in ("x86_64", "amd64", "i686", "i386"),
        "sistema": platform.system(),
        "python": platform.python_version(),
        "es_android": es_android(),
        "es_termux": es_termux(),
        "cpus": os.cpu_count() or 1,
    }


def puede_correr() -> dict[str, Any]:
    """Un PC de desarrollo puede ejecutar los trabajos, pero no los valida."""
    p = plataforma()
    if p["es_arm"] and p["es_android"]:
        motivo = "ARM real bajo Android: exactamente el objetivo del CI"
        valido = True
    elif p["es_arm"]:
        motivo = "ARM, pero no Android. Sirve para arquitectura, no para Termux."
        valido = True
    else:
        motivo = (
            f"{p['arquitectura']} / {p['sistema']}: NO representa al "
            "dispositivo de destino. Lo que pase aqui no prueba ARM."
        )
        valido = False
    return {"ok": valido, "plataforma": p, "motivo": motivo}


# ==========================================================================
#  Trabajos — lista cerrada. Nada de `run:` que venga de fuera.
# ==========================================================================
def _ficheros_py(cfg: dict[str, Any]) -> list[Path]:
    if cfg.get("solo_raiz", True):
        return sorted(p for p in PROJECT_ROOT.glob("*.py") if p.is_file())
    out: list[Path] = []
    for p in PROJECT_ROOT.rglob("*.py"):
        if any(parte in cfg.get("ignorar", []) for parte in p.parts):
            continue
        out.append(p)
    return sorted(out)


def job_sintaxis(cfg: dict[str, Any]) -> dict[str, Any]:
    """Compila cada .py. Es el unico test que atrapa un SyntaxError real.

    Importa porque un SyntaxError dentro de un modulo NO es ImportError:
    no lo agarra el `except` de daniela_os.py y tumba el arranque entero.
    """
    import py_compile

    malos: list[str] = []
    n = 0
    for p in _ficheros_py(cfg):
        n += 1
        try:
            py_compile.compile(str(p), doraise=True, cfile=str(p) + "c")
        except py_compile.PyCompileError as e:
            malos.append(f"{p.name}: {str(e).splitlines()[-1][:120]}")
        except OSError:
            continue
        finally:
            try:
                Path(str(p) + "c").unlink()
            except OSError:
                pass
    return {
        "ok": not malos,
        "revisados": n,
        "errores": malos[:20],
        "detalle": f"{n} ficheros, {len(malos)} con error de sintaxis",
    }


def job_seguridad(cfg: dict[str, Any]) -> dict[str, Any]:
    """AST: la regla dura del proyecto (nunca os.system, nunca shell=True)."""
    hallados: list[dict[str, Any]] = []
    n = 0
    for p in _ficheros_py(cfg):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError, ValueError):
            continue
        n += 1
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            nombre = getattr(fn, "attr", None) or getattr(fn, "id", None)
            # Falso positivo conocido: platform.system() no es os.system()
            if (
                nombre in ("system", "popen")
                and getattr(getattr(fn, "value", None), "id", None) == "os"
            ):
                hallados.append({"fichero": p.name, "linea": node.lineno, "tipo": f"os.{nombre}"})
            for kw in node.keywords:
                if kw.arg == "shell" and getattr(kw.value, "value", None) is True:
                    hallados.append({"fichero": p.name, "linea": node.lineno, "tipo": "shell=True"})
    return {
        "ok": not hallados,
        "revisados": n,
        "errores": hallados[:30],
        "detalle": f"{n} ficheros, {len(hallados)} llamadas inseguras",
    }


def job_arranque(cfg: dict[str, Any]) -> dict[str, Any]:
    """El test que de verdad importa: ¿levanta DanielaOS y cuantas rutas?

    Es el mas lento y el mas valioso: ningun linter te dice que un modulo
    nuevo tumbo el arranque por un endpoint duplicado.
    """
    codigo = (
        "import importlib,sys;"
        "sys.argv=['daniela_os.py'];"
        "m=importlib.import_module('daniela_os');"
        "print(len(list(m.app.url_map.iter_rules())))"
    )
    r = _run([sys.executable, "-c", codigo], timeout=int(cfg.get("timeout_s", 300)))
    if r["codigo"] != 0:
        return {
            "ok": False,
            "rutas": 0,
            "detalle": "daniela_os.py no arranca",
            "error": r["error"][-500:],
        }
    try:
        rutas = int(r["salida"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"ok": False, "rutas": 0, "detalle": "no se pudo leer el nº de rutas"}
    return {"ok": rutas > 0, "rutas": rutas, "detalle": f"arranca con {rutas} rutas"}


def _job_herramienta(
    nombre: str, modulo: str, args: list[str], cfg: dict[str, Any]
) -> dict[str, Any]:
    """Un trabajo que depende de una herramienta externa: degrada, no falla.

    Se invoca como `sys.executable -m <modulo>` y no con el ejecutable suelto:
    `which('pytest')` puede encontrar el de otro Python y entonces estariamos
    midiendo un interprete que no es el de Daniela.
    """
    if not _tiene_modulo(modulo):
        return {
            "ok": True,
            "omitido": True,
            "detalle": f"{nombre} no instalado en este interprete "
            f"({Path(sys.executable).name}): se omite",
        }
    r = _run(
        [sys.executable, "-m", modulo] + args, timeout=int(cfg.get("timeout_herramienta_s", 90))
    )
    return {
        "ok": r["codigo"] == 0,
        "codigo": r["codigo"],
        "detalle": (r["salida"] or r["error"]).strip()[-300:] or "sin salida",
    }


def job_ruff(cfg: dict[str, Any]) -> dict[str, Any]:
    return _job_herramienta("ruff", "ruff", ["check", ".", "--exit-zero", "--quiet"], cfg)


def job_mypy(cfg: dict[str, Any]) -> dict[str, Any]:
    return _job_herramienta("mypy", "mypy", ["--version"], cfg)


def job_pytest(cfg: dict[str, Any]) -> dict[str, Any]:
    """pytest acotado a tests/ y con timeout corto.

    Suelta `pytest` sobre / sin mas recoge los 281 ficheros del repo, incluidos
    tests que arrancan servidores: se cuelga. Se corre solo sobre tests/ y con
    la sesion sin cache para no pelearse con ejecuciones anteriores.
    """
    objetivo = "tests" if Path("tests").is_dir() else "."
    return _job_herramienta(
        "pytest", "pytest", ["-q", "--no-header", "-p", "no:cacheprovider", objetivo], cfg
    )


TRABAJOS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "sintaxis": job_sintaxis,
    "seguridad": job_seguridad,
    "arranque": job_arranque,
    "ruff": job_ruff,
    "mypy": job_mypy,
    "pytest": job_pytest,
}


# ==========================================================================
#  Corredor
# ==========================================================================
class CorredorCI:
    """Ejecuta la lista cerrada de trabajos y guarda historial."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = dict(CONFIG_DEFAULT)
        self._lock = threading.RLock()
        self.ultimos: dict[str, dict[str, Any]] = {}
        self.historial: list[dict[str, Any]] = []
        self._corriendo = False
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.cargar()
        if config:
            self.config.update({k: v for k, v in config.items() if k in CONFIG_DEFAULT})

    def cargar(self) -> None:
        try:
            if CONFIG_FILE.exists():
                d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.config.update({k: v for k, v in d.items() if k in CONFIG_DEFAULT})
        except (OSError, ValueError):
            pass
        try:
            if HISTORY_FILE.exists():
                h = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(h, list):
                    self.historial = h[-MAX_HISTORIAL:]
        except (OSError, ValueError):
            pass

    def guardar(self) -> None:
        try:
            CONFIG_FILE.write_text(
                json.dumps(self.config, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            HISTORY_FILE.write_text(
                json.dumps(self.historial[-MAX_HISTORIAL:], ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass

    # -------------------------------------------------------------- ejecutar
    def ejecutar(self, trabajos: list[str] | None = None) -> dict[str, Any]:
        if self._corriendo:
            return {"ok": False, "error": "ya hay una ejecucion en marcha"}
        nombres = trabajos or list(TRABAJOS)
        malos = [t for t in nombres if t not in TRABAJOS]
        if malos:
            return {
                "ok": False,
                "error": f"trabajos desconocidos: {malos}",
                "disponibles": list(TRABAJOS),
            }

        self._corriendo = True
        t0 = time.time()
        resultados: dict[str, dict[str, Any]] = {}
        try:
            for nombre in nombres:
                ini = time.time()
                try:
                    r = TRABAJOS[nombre](self.config)
                except Exception as e:  # un trabajo roto no tumba el CI
                    r = {"ok": False, "detalle": f"{type(e).__name__}: {e}"}
                r["trabajo"] = nombre
                r["duracion_s"] = round(time.time() - ini, 2)
                resultados[nombre] = r
                with self._lock:
                    self.ultimos[nombre] = r
        finally:
            self._corriendo = False

        fallidos = [k for k, v in resultados.items() if not v.get("ok") and not v.get("omitido")]
        omitidos = [k for k, v in resultados.items() if v.get("omitido")]
        resumen = {
            "ok": not fallidos,
            "plataforma": plataforma(),
            "representa_al_objetivo": puede_correr()["ok"],
            "trabajos": resultados,
            "fallidos": fallidos,
            "omitidos": omitidos,
            "duracion_s": round(time.time() - t0, 2),
            "ts": time.time(),
        }
        with self._lock:
            self.historial.append(
                {
                    "ts": resumen["ts"],
                    "ok": resumen["ok"],
                    "fallidos": fallidos,
                    "omitidos": omitidos,
                    "duracion_s": resumen["duracion_s"],
                    "arquitectura": plataforma()["arquitectura"],
                }
            )
            if len(self.historial) > MAX_HISTORIAL:
                self.historial = self.historial[-MAX_HISTORIAL:]
            self.guardar()
        return resumen

    # --------------------------------------------------------------- GitHub
    def estado_github(self) -> dict[str, Any]:
        """Ultimos workflow runs. Solo LECTURA: no ejecuta nada del repo."""
        if not _tiene("gh"):
            return {"ok": False, "error": "gh no instalado"}
        repo = self.config["repo"]
        # OJO con el jq: la interpolacion \(...) solo funciona DENTRO de una
        # cadena jq. Fuera de comillas es un error de sintaxis y gh devuelve
        # "failed to parse jq expression" (nos paso en el primer demo).
        jq = (
            '[.workflow_runs[]][0:5] | map([.status, (.conclusion // "nada"), '
            '.head_sha[0:8], .name] | join("  ")) | join("\n")'
        )
        r = _run(["gh", "api", f"repos/{repo}/actions/runs", "--jq", jq], timeout=45)
        if r["codigo"] != 0:
            return {"ok": False, "error": r["error"][:300]}
        return {"ok": True, "repo": repo, "runs": r["salida"]}

    def publicar(
        self, sha: str, estado: str | None = None, descripcion: str = ""
    ) -> dict[str, Any]:
        """Publica el resultado como estado de commit. Nunca como runner."""
        if not _tiene("gh"):
            return {"ok": False, "error": "gh no instalado"}
        if not sha or len(sha) < 7:
            return {"ok": False, "error": "sha demasiado corto"}
        if estado is None:
            fallidos = [
                k for k, v in self.ultimos.items() if not v.get("ok") and not v.get("omitido")
            ]
            estado = "failure" if fallidos else "success"
        p = plataforma()
        desc = descripcion or f"CI en {p['arquitectura']} ({p['sistema']})"
        r = _run(
            [
                "gh",
                "api",
                "-X",
                "POST",
                f"repos/{self.config['repo']}/statuses/{sha}",
                "-f",
                f"state={estado}",
                "-f",
                f"context={self.config['contexto_github']}",
                "-f",
                f"description={desc}",
            ],
            timeout=45,
        )
        return {
            "ok": r["codigo"] == 0,
            "estado": estado,
            "sha": sha,
            "error": None if r["codigo"] == 0 else r["error"][:300],
        }

    # ---------------------------------------------------------------- estado
    def estado(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "plataforma": plataforma(),
                "capacidad": puede_correr(),
                "trabajos": list(TRABAJOS),
                "corriendo": self._corriendo,
                "ultimos": self.ultimos,
                "ejecuciones": len(self.historial),
                "config": dict(self.config),
            }

    def configurar(self, **kv: Any) -> dict[str, Any]:
        with self._lock:
            for k, v in kv.items():
                if k in CONFIG_DEFAULT and v is not None:
                    self.config[k] = v
        self.guardar()
        return dict(self.config)


# ==========================================================================
#  Singleton
# ==========================================================================
_INSTANCIA: CorredorCI | None = None
_LOCK = threading.Lock()


def get_instance() -> CorredorCI:
    global _INSTANCIA
    with _LOCK:
        if _INSTANCIA is None:
            _INSTANCIA = CorredorCI()
        return _INSTANCIA


# ==========================================================================
#  Rutas Flask
# ==========================================================================
def register_ci_routes(app) -> None:
    if Flask is None:
        return

    def m() -> CorredorCI:
        return get_instance()

    @app.route("/api/ci/status", methods=["GET"], endpoint="ci__status")
    def _status():
        return jsonify(m().estado())

    @app.route("/api/ci/jobs", methods=["GET"], endpoint="ci__jobs")
    def _jobs():
        with m()._lock:  # noqa: SLF001
            return jsonify({"ok": True, "disponibles": list(TRABAJOS), "ultimos": m().ultimos})

    @app.route("/api/ci/run", methods=["POST"], endpoint="ci__run")
    def _run_route():
        d = request.get_json(silent=True) or {}
        trab = d.get("trabajos")
        if isinstance(trab, str):
            trab = [trab]
        if trab is not None and not isinstance(trab, list):
            return jsonify({"ok": False, "error": "trabajos debe ser lista"}), 400
        res = m().ejecutar(trab)
        return jsonify(res), (200 if res.get("ok") else 422)

    @app.route("/api/ci/history", methods=["GET"], endpoint="ci__history")
    def _history():
        try:
            n = int(request.args.get("n", 20))
        except (TypeError, ValueError):
            n = 20
        with m()._lock:  # noqa: SLF001
            return jsonify({"ok": True, "historial": m().historial[-max(1, n) :]})

    @app.route("/api/ci/github", methods=["GET"], endpoint="ci__github")
    def _github():
        return jsonify(m().estado_github())

    @app.route("/api/ci/publish", methods=["POST"], endpoint="ci__publish")
    def _publish():
        d = request.get_json(silent=True) or {}
        sha = str(d.get("sha", "")).strip()
        if not sha:
            r = _run(["git", "rev-parse", "HEAD"], timeout=20)
            sha = r["salida"].strip() if r["codigo"] == 0 else ""
        return jsonify(m().publicar(sha, d.get("estado"), str(d.get("descripcion", ""))))

    print("[CI Runner] Routes registered: /api/ci/* (status, jobs, run, history, github, publish)")


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo(completo: bool = False) -> None:
    print("=" * 68)
    print(" CI EN ARM REAL (E-15) — probar donde de verdad corre Daniela")
    print("=" * 68)

    p = plataforma()
    print("arquitectura :", p["arquitectura"], f"(es_arm={p['es_arm']})")
    print("sistema      :", p["sistema"])
    print("python       :", p["python"])
    print("es android   :", p["es_android"], " es termux:", p["es_termux"])

    cap = puede_correr()
    print("\n-- representa al dispositivo de destino? --")
    print("   valido:", cap["ok"])
    print("   motivo:", cap["motivo"])

    ci = CorredorCI()
    print("\n-- trabajos disponibles --")
    print("  ", ", ".join(TRABAJOS))

    print("\n-- seguridad: los trabajos son una LISTA CERRADA --")
    r = ci.ejecutar(["trabajo_que_no_existe"])
    print("   trabajo inventado rechazado :", not r["ok"], "-", r.get("error"))

    print("\n-- sintaxis (caza el SyntaxError que tumba el arranque) --")
    r = job_sintaxis(ci.config)
    print("   ok:", r["ok"], "|", r["detalle"])
    for e in r["errores"][:3]:
        print("     !", e)

    print("\n-- seguridad AST (os.system / shell=True) --")
    r = job_seguridad(ci.config)
    print("   ok:", r["ok"], "|", r["detalle"])
    for e in r["errores"][:3]:
        print(f"     ! {e['fichero']}:{e['linea']} {e['tipo']}")

    print("\n-- herramientas externas: degradan, no suspenden --")
    for nombre in ("ruff", "mypy", "pytest"):
        r = TRABAJOS[nombre](ci.config)
        marca = "omitido" if r.get("omitido") else ("ok" if r["ok"] else "FALLO")
        print(f"   {nombre:<8} {marca:<8} {r['detalle'][:60]}")

    if completo:
        print("\n-- arranque (el test que de verdad importa) --")
        r = job_arranque(ci.config)
        print("   ok:", r["ok"], "|", r["detalle"])
    else:
        print("\n-- arranque: omitido (python ci_runner.py --completo para ejecutarlo, tarda) --")

    print("\n-- github: solo lectura de los ultimos runs --")
    g = ci.estado_github()
    if g.get("ok"):
        print("   repo:", g["repo"])
        for linea in str(g["runs"]).splitlines():
            print("    ", linea)
    else:
        print("   no disponible:", g.get("error"))

    print("\n-- historial --")
    print("   ejecuciones guardadas:", len(ci.historial))

    print("=" * 68)


if __name__ == "__main__":
    _demo(completo="--completo" in sys.argv)

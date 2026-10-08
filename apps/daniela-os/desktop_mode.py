#!/usr/bin/env python3
"""
desktop_mode.py — E-23 · El Pixel como ordenador
=================================================

El Pixel 8a declara `freeform_window_management` y
`activities_on_secondary_displays`: **puede funcionar como un escritorio**.
Con un cable USB-C a HDMI (o un adaptador barato) y Termux:X11, Daniela deja de
verse en 6 pulgadas y pasa a pantalla completa con teclado y raton Bluetooth.

Qué hace este modulo
--------------------
1. **Detecta** pantallas externas leyendo `dumpsys display` (sin root).
2. **Habilita** las opciones de escritorio con `settings put global`
   (escritorio, ventanas libres, forzar escritorio en pantallas externas).
3. **Prepara** la sesion X11: genera un script de arranque con el WM elegido y
   lo deja listo en `data/desktop/start-x11.sh`.
4. **Ajusta** densidad y resolucion con `wm` para que la interfaz no se vea
   como un movil estirado.

Degradacion honesta
-------------------
`settings put global` puede fallar sin `WRITE_SECURE_SETTINGS`. En ese caso el
modulo lo reporta y sigue: se puede conceder el permiso con
`adb shell pm grant com.termux android.permission.WRITE_SECURE_SETTINGS`
(desde un PC con depuracion USB), o escribiendo el valor a mano en Opciones de
desarrollador. **El modulo nunca falla en silencio.**

Rutas
-----
    GET  /api/pixel/desktop/status        pantallas, ajustes y sesion
    GET  /api/pixel/desktop/displays      pantallas detectadas
    POST /api/pixel/desktop/enable        habilita escritorio + ventanas libres
    POST /api/pixel/desktop/disable       lo deshace
    POST /api/pixel/desktop/density       ajusta densidad (wm density)
    POST /api/pixel/desktop/session       start / stop de la sesion X11
    POST /api/pixel/desktop/config        WM, resolucion, opciones
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "desktop"
CONFIG_FILE = DATA_DIR / "config.json"
START_SCRIPT = DATA_DIR / "start-x11.sh"

# Ajustes globales que activan el escritorio
AJUSTES = {
    "escritorio": "enable_desktop_mode",
    "forzar_externa": "force_desktop_mode_on_external_displays",
    "ventanas_libres": "enable_freeform_support",
}

CONFIG_DEFAULT: dict[str, Any] = {
    "wm": "xfce4",  # xfce4 | openbox | i3 | none
    "display": ":1",
    "resolucion": "1920x1080",
    "densidad": 240,
    "teclado_bluetooth": True,
}

COMANDOS_WM = {
    "xfce4": "startxfce4",
    "openbox": "openbox-session",
    "i3": "i3",
    "none": "xterm",
}


# ==========================================================================
#  Ejecucion sin shell
# ==========================================================================
def _run(args: list[str], timeout: int = 12) -> dict[str, Any]:
    try:
        r = subprocess.run(list(args), capture_output=True, timeout=timeout, shell=False)
        return {
            "ok": r.returncode == 0,
            "salida": (r.stdout or b"").decode("utf-8", "replace").strip(),
            "error": (r.stderr or b"").decode("utf-8", "replace").strip(),
        }
    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "salida": "", "error": str(e)}


def _settings_get(clave: str) -> str | None:
    r = _run(["settings", "get", "global", clave])
    if not r["ok"] or r["salida"] in ("null", "", "None"):
        return None
    return r["salida"]


def _settings_put(clave: str, valor: str) -> dict[str, Any]:
    r = _run(["settings", "put", "global", clave, valor])
    if r["ok"]:
        # Comprobamos que realmente se escribio
        return {"clave": clave, "valor": valor, "verificado": _settings_get(clave) == valor, **r}
    return {"clave": clave, "valor": valor, "verificado": False, **r}


# ==========================================================================
#  Pantallas
# ==========================================================================
def detectar_pantallas() -> list[dict[str, Any]]:
    """Parsea `dumpsys display` buscando pantallas y su estado."""
    r = _run(["dumpsys", "display"], timeout=15)
    if not r["ok"]:
        return []
    pantallas: list[dict[str, Any]] = []
    bloque = None
    for linea in r["salida"].splitlines():
        s = linea.strip()
        if s.startswith("Display "):
            bloque = {"id": s.split()[1].rstrip(":"), "estado": "", "tipo": ""}
            pantallas.append(bloque)
        elif bloque is not None:
            if "state=" in s:
                bloque["estado"] = s.split("state=")[1].split(",")[0].strip()
            elif "type=" in s and not bloque["tipo"]:
                bloque["tipo"] = s.split("type=")[1].split(",")[0].strip()
            elif "mDisplayId" in s and not bloque.get("id"):
                bloque["id"] = s.split("=")[1].strip()
            m = re.search(r"(\d{3,5})\s*x\s*(\d{3,5})", s)
            if m and "resolucion" not in bloque:
                bloque["resolucion"] = f"{m.group(1)}x{m.group(2)}"
    return [p for p in pantallas if p.get("id")][:10]


def pantalla_externa() -> bool:
    return len(detectar_pantallas()) > 1


# ==========================================================================
#  Sesion X11
# ==========================================================================
def generar_script(config: dict[str, Any]) -> Path:
    """Escribe el script que levanta el escritorio dentro de Termux."""
    wm = COMANDOS_WM.get(str(config.get("wm", "xfce4")), "startxfce4")
    display = str(config.get("display", ":1"))
    resolucion = str(config.get("resolucion", "1920x1080"))
    contenido = f"""#!/data/data/com.termux/files/usr/bin/bash
# Generado por desktop_mode.py (E-23) — {time.strftime("%F %T")}
# Uso: termux-x11 :1 -xstartup "$(pwd)/start-x11.sh"
set -e

export DISPLAY={display}
export PULSE_SERVER=tcp:127.0.0.1:4713
export XDG_RUNTIME_DIR=${{TMPDIR:-/data/data/com.termux/files/usr/tmp}}

# Ratón y teclado en pantalla para no depender del Bluetooth
matchbox-keyboard &>/dev/null &

# Prevenir el salvapantallas: en un escritorio molesta mas que ayuda
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true

# Si hay pantalla externa, ajustamos la resolucion
if command -v xrandr >/dev/null 2>&1; then
  xrandr --output HDMI-1 --mode {resolucion} 2>/dev/null || true
fi

exec {wm}
"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    START_SCRIPT.write_text(contenido, encoding="utf-8")
    try:
        START_SCRIPT.chmod(0o755)
    except OSError:
        pass
    return START_SCRIPT


def sesion_activa(display: str = ":1") -> bool:
    """Mira si existe el socket de X."""
    numero = display.lstrip(":").split(".")[0]
    return Path(f"/tmp/.X11-unix/X{numero}").exists()


# ==========================================================================
#  Estado
# ==========================================================================
class DesktopMode:
    def __init__(self) -> None:
        self.config = dict(CONFIG_DEFAULT)
        self.ultimo_ajuste: dict[str, Any] = {}
        self.eventos: list[dict[str, Any]] = []
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cargar()

    def _cargar(self) -> None:
        if CONFIG_FILE.exists():
            try:
                d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.config.update({k: v for k, v in d.items() if k in CONFIG_DEFAULT})
            except Exception:
                pass

    def _guardar(self) -> None:
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.config, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(CONFIG_FILE)

    def configurar(self, **kv: Any) -> dict[str, Any]:
        for k, v in kv.items():
            if k in self.config and isinstance(v, type(self.config[k])):
                self.config[k] = v
        self._guardar()
        return dict(self.config)

    def _evento(self, tipo: str, detalle: Any) -> None:
        self.eventos.append({"t": time.time(), "tipo": tipo, "detalle": detalle})
        self.eventos = self.eventos[-100:]

    def habilitar(self) -> dict[str, Any]:
        resultados = {nombre: _settings_put(clave, "1") for nombre, clave in AJUSTES.items()}
        self.ultimo_ajuste = resultados
        self._evento("enable", {k: v.get("verificado") for k, v in resultados.items()})
        return resultados

    def deshabilitar(self) -> dict[str, Any]:
        resultados = {nombre: _settings_put(clave, "0") for nombre, clave in AJUSTES.items()}
        self.ultimo_ajuste = resultados
        self._evento("disable", {k: v.get("verificado") for k, v in resultados.items()})
        return resultados

    def densidad(self, dpi: int) -> dict[str, Any]:
        dpi = max(120, min(640, int(dpi)))
        r = _run(["wm", "density", str(dpi)])
        self.config["densidad"] = dpi
        self._guardar()
        self._evento("density", dpi)
        return {"dpi": dpi, **r}

    def estado(self) -> dict[str, Any]:
        return {
            "ajustes": {n: _settings_get(c) for n, c in AJUSTES.items()},
            "pantallas": detectar_pantallas(),
            "pantalla_externa": pantalla_externa(),
            "sesion_x11": sesion_activa(str(self.config["display"])),
            "config": dict(self.config),
            "script": str(START_SCRIPT) if START_SCRIPT.exists() else None,
            "wm_disponible": _run(["which", COMANDOS_WM.get(str(self.config["wm"]), "startxfce4")])[
                "ok"
            ],
            "eventos": self.eventos[-10:],
        }


_instancia: DesktopMode | None = None


def get_instance() -> DesktopMode:
    global _instancia
    if _instancia is None:
        _instancia = DesktopMode()
    return _instancia


# --------------------------------------------------------------------------
#  Rutas Flask
# --------------------------------------------------------------------------
def register_desktop_routes(app) -> None:
    if Flask is None:
        return

    def d() -> DesktopMode:
        return get_instance()

    @app.route("/api/pixel/desktop/status", methods=["GET"], endpoint="desktop__status")
    def _status():
        return jsonify({"ok": True, "desktop": d().estado()})

    @app.route("/api/pixel/desktop/displays", methods=["GET"], endpoint="desktop__displays")
    def _displays():
        return jsonify({"ok": True, "pantallas": detectar_pantallas()})

    @app.route("/api/pixel/desktop/enable", methods=["POST"], endpoint="desktop__enable")
    def _enable():
        return jsonify(
            {"ok": True, "ajustes": d().habilitar(), "script": str(generar_script(d().config))}
        )

    @app.route("/api/pixel/desktop/disable", methods=["POST"], endpoint="desktop__disable")
    def _disable():
        return jsonify({"ok": True, "ajustes": d().deshabilitar()})

    @app.route("/api/pixel/desktop/density", methods=["POST"], endpoint="desktop__density")
    def _density():
        body = request.get_json(silent=True) or {}
        return jsonify({"ok": True, **d().densidad(int(body.get("dpi", 240)))})

    @app.route("/api/pixel/desktop/session", methods=["POST"], endpoint="desktop__session")
    def _session():
        body = request.get_json(silent=True) or {}
        accion = str(body.get("accion", "status")).lower()
        if accion == "start":
            ruta = generar_script(d().config)
            return jsonify(
                {
                    "ok": True,
                    "accion": "start",
                    "script": str(ruta),
                    "siguiente": f"termux-x11 {d().config['display']} -xstartup {ruta}",
                }
            )
        if accion == "stop":
            r = _run(["pkill", "-f", "termux-x11"])
            return jsonify({"ok": True, "accion": "stop", **r})
        return jsonify(
            {"ok": True, "accion": "status", "activa": sesion_activa(str(d().config["display"]))}
        )

    @app.route("/api/pixel/desktop/config", methods=["POST"], endpoint="desktop__config")
    def _config():
        body = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "config": d().configurar(**body)})

    print(
        "[Desktop Mode] Routes registered: /api/pixel/desktop/* "
        "(status, displays, enable, disable, density, session, config)"
    )


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" DESKTOP MODE (E-23) — el Pixel como ordenador")
    print("=" * 68)
    d = DesktopMode()
    print("\n-- pantallas detectadas --")
    p = detectar_pantallas()
    print("  ", p if p else "ninguna (sin HDMI conectado)")

    print("\n-- ajustes actuales --")
    for nombre, clave in AJUSTES.items():
        print(f"   {nombre:16s} {clave:44s} = {_settings_get(clave)}")

    print("\n-- script de sesion generado --")
    ruta = generar_script(d.config)
    print("   ", ruta)
    print("   ", "-" * 60)
    for linea in ruta.read_text(encoding="utf-8").splitlines()[:8]:
        print("   ", linea)
    print("=" * 68)


if __name__ == "__main__":
    _demo()

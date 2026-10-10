#!/usr/bin/env python3
"""
termux_deployer.py — Construye y sube DanielaOS al Pixel sin cables raros.

Hace dos cosas:
  1. BUILD: copia los modulos necesarios a un directorio limpio y lo VERIFICA
     arrancando la app aislada (para no subir nada roto al movil).
  2. PUSH:  sube ese directorio al Pixel por adb a /sdcard/DanielaOS/deploy.

Seguridad: solo subprocess.run(list_args). Nada de os.system() ni shell=True.

Uso:
    python skills/connectors/android/termux_deployer.py build
    python skills/connectors/android/termux_deployer.py push
    python skills/connectors/android/termux_deployer.py all

Lado PC/admin (ADR-022): este script vive en skills/, pero los modulos que
empaqueta son los del arbol de cliente/fuente unica, no de esta carpeta.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "daniela-os"  # fuente unica de los modulos que viajan al movil (ADR-022 §4)
BUNDLE = ROOT / "phone_deploy"  # SALIDA DE BUILD, no fuente

# Modulos que deben vivir en el telefono.
# Se excluyen los pesados/PC (sil_engine, google_free_tier_automations) y los
# que arrastran errores de sintaxis (daniela_self_improvement).
MODULES: list[str] = [
    "daniela_os.py",             # entrypoint (218 rutas)
    "safe_exec.py",              # utilidad de ejecucion segura
    "daniela_os_core.py",           # nucleo
    # Fase 5
    "daemon_24_7.py",
    "git_brain_sync.py",
    "auto_sanitizer.py",
    # Fase 6
    "daniela_mobile_core.py",
    "context_engine.py",
    "blackbox_forense.py",
    # Fase 7
    "native_ui.py",
    "ir_bridge.py",
    "nfc_automation.py",
    "serial_bridge.py",
    # Fase 4 (registrados por daniela_os)
    "sensor_stream_live.py",
    "adb_mirror.py",
    "clipboard_sync.py",
    "fcm_real_bridge.py",
    "file_sync_daemon.py",
    "geofence_engine.py",
    "iot_real_integration.py",
    # Hub PC<->Pixel (vive en el arbol cliente, ADR-022 §4)
    "frontend/apps/android-app/mobile-app/bridges/pixel/pixel_bridge_hub.py",
    "pixel_second_screen.py",
    "screen_ai_vision.py",
    "security_camera.py",
    "voice_pipeline.py",
    # Gateway Termux:API (vive en el arbol cliente, ADR-022 §4)
    "frontend/apps/android-app/mobile-app/api/termux_api_gateway.py",
    # Fase 8 — malla offline-first
    "daniela_mesh.py",
    # Fase 10 — máximo esplendor (hardware que estaba declarado y sin usar)
    "wifi_rtt.py",               # E-19 posicion interior sin GPS
    "wifi_aware.py",             # E-20 malla sin infraestructura
    "context_hub.py",            # E-21 wakelock battery-aware
    "silicon_vault.py",          # E-22 secretos en StrongBox
    "desktop_mode.py",           # E-23 el Pixel como ordenador
    "live_wallpaper.py",         # E-24 fondo que cambia con el contexto
    "nfc_hce.py",                # E-25 el movil como llave
    "stereo_vision.py",          # E-26 profundidad sin OpenCV
]

TEMPLATES: list[str] = [
    "index.html",
    "index_sovereign_master.html",
    "pixel_dashboard.html",
]

EXTRA_FILES: list[str] = [
    "install.sh",
    "requirements.txt",
    "LEEME.txt",
    # Utilidades de auditoria y limpieza. Sin estar aqui, `build()` las
    # borraba del bundle al vaciar el directorio y aparecian como ficheros
    # eliminados en git sin que nadie los hubiera quitado.
    "optimizar_telefono.sh",
    "limpieza_final.sh",
]

ADB_CANDIDATES = [
    "adb",
    r"C:\ProgramData\chocolatey\lib\adb\tools\platform-tools\adb.exe",
    str(Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe"),
]

PHONE_DEST = "/sdcard/DanielaOS/deploy"


def _run(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    """Ejecuta sin shell. Devuelve el CompletedProcess (nunca lanza)."""
    return subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )


def build(verbose: bool = True) -> int:
    """Arma el bundle y lo verifica arrancandolo aislado."""
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    (BUNDLE / "templates").mkdir(parents=True)
    (BUNDLE / "data").mkdir(parents=True)

    faltan = []
    for m in MODULES:
        # Los nombres con "/" son rutas relativas al repo (fuente unica
        # fuera de daniela-os/, ej. el gateway del arbol cliente); el
        # bundle se mantiene FLAT porque asi corre en Termux.
        src = (REPO / m) if "/" in m else (ROOT / m)
        dst = BUNDLE / Path(m).name
        if src.exists():
            shutil.copy2(src, dst)
        else:
            faltan.append(m)
    for t in TEMPLATES:
        src = ROOT / "templates" / t
        if src.exists():
            shutil.copy2(src, BUNDLE / "templates" / t)
    faltan_extra = []
    for f in EXTRA_FILES:
        # La fuente de verdad es la RAIZ. El bundle se vacia en cada build,
        # asi que un fichero que solo viva en phone_deploy/ desaparece sin
        # avisar y termina borrado del repo en el siguiente `git add -A`.
        src = ROOT / f if (ROOT / f).exists() else ROOT / "phone_deploy" / f
        if src.exists():
            shutil.copy2(src, BUNDLE / f)
        else:
            faltan_extra.append(f)

    if faltan:
        print(f"[build] AVISO, faltan {len(faltan)} modulos: {faltan}")
    if faltan_extra:
        # Antes esto se callaba: el bundle salia sin install.sh y el
        # telefono se quedaba sin forma de instalar. Ahora se ve.
        print(f"[build] AVISO, faltan {len(faltan_extra)} extras "
              f"(deben estar en la raiz): {faltan_extra}")

    n = len(list(BUNDLE.glob("*.py")))
    size = sum(f.stat().st_size for f in BUNDLE.rglob("*") if f.is_file())
    print(f"[build] {n} modulos · {size/1024:.0f} KB en {BUNDLE}")

    # Verificacion: arrancar la app DENTRO del bundle para no subir nada roto
    code = (
        "from daniela_os import app;"
        "print('ROUTES', len(list(app.url_map.iter_rules())))"
    )
    res = _run([sys.executable, "-c", code], timeout=180)
    out = (res.stdout or "") + (res.stderr or "")
    routes = None
    for line in out.splitlines():
        if line.startswith("ROUTES"):
            routes = int(line.split()[1])
    if res.returncode != 0 or routes is None:
        print("[build] FALLO la verificacion:")
        print(out[-2000:])
        return 1
    print(f"[build] verificado: arranca con {routes} rutas")
    return 0


def find_adb() -> str | None:
    for c in ADB_CANDIDATES:
        try:
            r = _run([c, "version"], timeout=20)
            if r.returncode == 0:
                return c
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def push(verbose: bool = True) -> int:
    """Sube el bundle al Pixel por adb."""
    adb = find_adb()
    if not adb:
        print("[push] no encontre adb en el PATH ni en las rutas conocidas")
        return 1
    print(f"[push] usando {adb}")

    _run([adb, "start-server"], timeout=60)
    r = _run([adb, "devices"], timeout=60)
    devices = [ln for ln in (r.stdout or "").splitlines() if "\tdevice" in ln]
    if not devices:
        print("[push] no hay ningun dispositivo con depuracion USB autorizada")
        return 1
    print(f"[push] dispositivo: {devices[0].split()[0]}")

    # OJO con la semantica de `adb push`: si el destino ya es un directorio,
    # adb mete el directorio DENTRO (…/deploy/phone_deploy) en vez de
    # fusionarlo. La primera vez colo porque el destino no existia; la
    # segunda anida. El "/." hace que suba el CONTENIDO, que es lo que
    # se quiere siempre.
    r = _run([adb, "push", str(BUNDLE) + "/.", PHONE_DEST], timeout=600)
    print((r.stdout or r.stderr or "").strip()[-800:])

    ls = _run([adb, "shell", "ls", "-1", f"{PHONE_DEST}/*.py"], timeout=60)
    n = len([ln for ln in (ls.stdout or "").splitlines() if ln.strip().endswith(".py")])
    print(f"[push] modulos en el telefono: {n}")
    return 0 if r.returncode == 0 and n else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Despliega DanielaOS en el Pixel")
    p.add_argument("accion", choices=["build", "push", "all"], nargs="?", default="all")
    args = p.parse_args()

    if args.accion in ("build", "all"):
        if build() != 0:
            return 1
    if args.accion in ("push", "all"):
        if push() != 0:
            return 1
    if args.accion == "all":
        print("\nAhora abre Termux en el Pixel y ejecuta:")
        print(f"    bash {PHONE_DEST}/install.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())

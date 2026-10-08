#!/usr/bin/env python3
"""
aig Mobile App - Unified Entry Point
=====================================
Punto de entrada unico de la app movil: PWA + servicios edge + Pixel bridge.

Uso:
    python mobile-app/main.py                # Todo (por defecto)
    python mobile-app/main.py --bridge       # Solo el Pixel bridge
    python mobile-app/main.py --gateway      # Solo el Termux API gateway
    python mobile-app/main.py --mobile       # Solo la PWA
    python mobile-app/main.py --all          # Igual que sin argumentos

Estructura (unificacion 2026-09-29, antes android_app/):
    mobile-app/services/  mobile-app/bridges/  mobile-app/core/
    mobile-app/api/
"""
import argparse
import os
import sys
from pathlib import Path

# `mobile-app/` no puede ser paquete Python (lleva guion), asi que sus
# subpaquetes (services, bridges, core, api, pixel, phone_deploy) se importan
# EN PLANO. Para eso este directorio va el PRIMERO de sys.path y la raiz del
# repo la segunda (gev, paths, daniela, ...).
#
# Ojo con `core`: gana `mobile-app/core` (los servicios edge) dentro de este
# proceso; los modulos de `core/` de la raiz se piden por su nombre plano
# (`from paths import ...`), que sigue resolviendose por la raiz del repo.
MOBILE_APP_DIR = Path(__file__).resolve().parent  # <repo>/mobile-app
PROJECT_ROOT = MOBILE_APP_DIR.parent               # <repo>
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(MOBILE_APP_DIR))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # dotenv not installed, use os.environ


def _app_daniela_os():
    """Devuelve la app Flask de Daniela OS, si es posible cargarla.

    `gev/daniela-os/` lleva guion: no es importable como modulo, asi que
    se carga por ruta con importlib (mismo truco que usa el propio visor).
    Cualquier fallo deja el bridge en modo autonomo.
    """
    try:
        from gev.daniela_os.server import app  # type: ignore[import-not-found]
        return app
    except ImportError:
        pass

    import importlib.util

    ruta = PROJECT_ROOT / "gev" / "daniela-os" / "server.py"
    if not ruta.is_file():
        raise ImportError(f"no encuentro el servidor de Daniela OS en {ruta}")
    spec = importlib.util.spec_from_file_location("gev_daniela_os_server", ruta)
    if spec is None or spec.loader is None:
        raise ImportError(f"no puedo cargar {ruta}")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.app


def run_bridge():
    """Run Pixel Bridge Hub."""
    from bridges.pixel import PixelBridgeHub

    bridge = PixelBridgeHub()
    print("[PixelBridge] Starting bridge hub...")
    print(f"[PixelBridge] Known IPs: {bridge._discover() or 'discovering...'}")

    # Register with Daniela OS
    try:
        daniela_app = _app_daniela_os()
        from bridges.pixel import register_pixel_routes
        register_pixel_routes(daniela_app)
        print("[PixelBridge] Routes registered with Daniela OS")
    except Exception as exc:  # noqa: BLE001 - el bridge tiene que sobrevivir
        print(f"[PixelBridge] Daniela OS not available ({exc}), running standalone")

    # Keep alive
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[PixelBridge] Shutting down...")


def run_gateway():
    """Run Termux API Gateway."""
    os.chdir(MOBILE_APP_DIR / "api")
    from api.termux_api_gateway import app

    port = int(os.getenv("PIXEL_GATEWAY_PORT", "8082"))
    print(f"[TermuxGateway] Starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)


def run_mobile():
    """Serve mobile PWA."""
    import http.server
    import socketserver

    os.chdir(MOBILE_APP_DIR)
    port = int(os.getenv("MOBILE_APP_PORT", "8095"))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"[MobileApp] Serving PWA on http://localhost:{port}")
        httpd.serve_forever()


def run_all():
    """Run all components."""
    import threading
    import time

    print("[aig Mobile] Starting all components...")

    # Start bridge in background
    bridge_thread = threading.Thread(target=run_bridge, daemon=True)
    bridge_thread.start()
    time.sleep(2)

    # Start gateway in background
    gateway_thread = threading.Thread(target=run_gateway, daemon=True)
    gateway_thread.start()
    time.sleep(2)

    # Start mobile app (blocking)
    run_mobile()


def main():
    parser = argparse.ArgumentParser(description="aig Mobile App")
    parser.add_argument("--bridge", action="store_true", help="Run Pixel bridge only")
    parser.add_argument("--gateway", action="store_true", help="Run Termux API gateway only")
    parser.add_argument("--mobile", action="store_true", help="Run mobile PWA server only")
    parser.add_argument("--all", action="store_true", help="Run all components")

    args = parser.parse_args()

    if args.bridge:
        run_bridge()
    elif args.gateway:
        run_gateway()
    elif args.mobile:
        run_mobile()
    elif args.all:
        run_all()
    else:
        # Default: run all
        run_all()


if __name__ == "__main__":
    main()
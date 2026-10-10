#!/usr/bin/env python3
"""
aig Android App - Quick Start
====================================
Run the unified Android app with Pixel integration.

Usage:
    python run.py                    # Run all services
    python run.py --bridge           # Pixel bridge only
    python run.py --gateway          # Termux gateway only
    python run.py --mobile           # Mobile PWA only
    python run.py --docker           # Build and run with Docker
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANDROID_APP_DIR = Path(__file__).parent


def run_bridge():
    """Run Pixel bridge hub."""
    os.chdir(ANDROID_APP_DIR)
    # `mobile-app/` no es paquete (guion): va el PRIMERO de PYTHONPATH y la
    # raiz del repo la segunda, igual que en main.py.
    pythonpath = os.pathsep.join([str(ANDROID_APP_DIR), str(PROJECT_ROOT)])
    subprocess.run([
        sys.executable, "-m", "bridges.pixel.pixel_bridge_hub"
    ], env={**os.environ, "PYTHONPATH": pythonpath})


def run_gateway():
    """Run Termux API gateway."""
    os.chdir(Path(__file__).parent / "api")
    subprocess.run([
        sys.executable, "termux_api_gateway.py"
    ], env=os.environ)


def run_mobile():
    """Run mobile PWA server."""
    import http.server
    import socketserver
    os.chdir(ANDROID_APP_DIR)  # aqui ya vive la PWA (index.html, js/, css/)
    int(os.getenv("MOBILE_APP_PORT", "8095"))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 8095), handler) as httpd:
        print("[MobileApp] Serving PWA on http://localhost:8095")
        httpd.serve_forever()


def run_docker():
    """Build and run with Docker Compose."""
    os.chdir(Path(__file__).parent)
    subprocess.run([
        "docker", "compose", "-f", "docker-compose.android.yml", "up", "-d", "--build"
    ])


def run_all():
    """Run all components."""
    import threading
    import time
    
    print("[aig Android] Starting all components...")
    
    # Start bridge in background thread
    bridge_thread = threading.Thread(target=run_bridge, daemon=True)
    bridge_thread.start()
    time.sleep(2)
    
    # Start gateway in background thread
    gateway_thread = threading.Thread(target=run_gateway, daemon=True)
    gateway_thread.start()
    time.sleep(2)
    
    # Run mobile app (blocking)
    run_mobile()


def main():
    parser = argparse.ArgumentParser(description="aig Android App")
    parser.add_argument("--bridge", action="store_true", help="Run Pixel bridge only")
    parser.add_argument("--gateway", action="store_true", help="Run Termux API gateway only")
    parser.add_argument("--mobile", action="store_true", help="Run mobile PWA server only")
    parser.add_argument("--docker", action="store_true", help="Build and run with Docker")
    parser.add_argument("--all", action="store_true", help="Run all components")
    
    args = parser.parse_args()
    
    if args.bridge:
        run_bridge()
    elif args.gateway:
        run_gateway()
    elif args.mobile:
        run_mobile()
    elif args.docker:
        run_docker()
    elif args.all:
        run_all()
    else:
        # Default: run all
        run_all()


if __name__ == "__main__":
    main()
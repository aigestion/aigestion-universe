#!/usr/bin/env python3
"""Monorepo inventory + health probe for aigestion-universe.

Lists every app/package, the canonical service->port map,
and (optionally) probes localhost ports for liveness.

Usage:
    python scripts/inventory.py            # structure only
    python scripts/inventory.py --probe    # also probe ports (fast, 1s timeout)
"""
from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Canonical service map: (name, port, kind, path)
SERVICES: list[tuple[str, int, str, str]] = [
    ("caddy", 80, "proxy", "Caddyfile"),
    ("caddy-tls", 443, "proxy", "Caddyfile"),
    ("daniela-shell", 3000, "app", "apps/daniela-shell"),
    ("landing", 3001, "app", "apps/landing"),
    ("grafana", 3000, "observability", "configs/grafana"),
    ("tempo", 3200, "observability", "configs/tempo"),
    ("loki", 3100, "observability", "configs/loki"),
    ("prometheus", 9090, "observability", "configs/prometheus"),
    ("daniela-core", 9200, "backend", "packages/daniela-core"),
    ("hermes-api", 9300, "protected", "-"),
    ("hermes-dash", 3200, "protected", "-"),
    ("infra", 9700, "protected", "-"),
    ("perf", 9998, "protected", "-"),
    ("postgres", 5432, "data", "docker-compose.yml"),
    ("redis", 6379, "data", "docker-compose.yml"),
    ("daniela-tools-gateway", 8083, "backend", "apps/daniela-tools-gateway"),
    ("daniela-sandbox", 8090, "backend", "apps/daniela-sandbox"),
    ("mobile-pwa-edge", 9800, "backend", "apps/mobile-pwa/services"),
]


def probe(port: int, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def inventory() -> list[dict]:
    rows = []
    for name, port, kind, path in SERVICES:
        exists = (path == "-") or (ROOT / path).exists()
        rows.append({"service": name, "port": port, "kind": kind, "path": path, "present": exists})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="aigestion-universe inventory")
    ap.add_argument("--probe", action="store_true", help="probe localhost ports")
    args = ap.parse_args()

    rows = inventory()
    print(f"{'SERVICE':24} {'PORT':>6} {'KIND':14} {'PATH':28} {'UP' if args.probe else 'PRESENT'}")
    print("-" * 90)
    for r in rows:
        if args.probe:
            # Only probe non-protected local ports to avoid noise.
            status = "up" if probe(r["port"]) else "--"
        else:
            status = "yes" if r["present"] else "MISSING"
        print(f"{r['service']:24} {r['port']:>6} {r['kind']:14} {r['path']:28} {status}")

    # Apps/packages file counts
    print()
    print("APPS/PACKAGES")
    print("-" * 90)
    for section in ("apps", "packages"):
        base = ROOT / section
        if not base.exists():
            continue
        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            count = sum(1 for _ in child.rglob("*") if _.is_file()
                        and "node_modules" not in _.parts
                        and "__pycache__" not in _.parts
                        and ".git" not in _.parts)
            print(f"  {section}/{child.name}/ -> {count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

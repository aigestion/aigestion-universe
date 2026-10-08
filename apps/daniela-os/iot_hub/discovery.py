"""Descubrimiento de hosts en la intranet.

Estrategia: ``nmap -sn`` si esta instalado; si no, ping-sweep stdlib
(subprocess ping en paralelo). Resultado persistido en
``data/iot/inventory.json`` con ``last_seen``/``fuente`` por host.
"""

from __future__ import annotations

import ipaddress
import json
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from iot_hub import config

MAX_SCAN_HOSTS = 1024


def parse_nmap_grepable(text: str) -> list[dict]:
    """Parsea la salida ``-oG`` de ``nmap -sn`` en una lista de hosts."""
    hosts: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Host: "):
            parts = line.split()
            if len(parts) < 2:
                continue
            is_up = "Status: Up" in line
            if not is_up:
                current = None
                continue
            current = {"ip": parts[1], "status": "up", "mac": "", "vendor": ""}
            hosts.append(current)
        elif current is not None and line.startswith("MAC Address:"):
            # "MAC Address: AA:BB:CC:DD:EE:FF (Vendor)"
            rest = line[len("MAC Address:") :].strip()
            mac = rest.split(" ")[0]
            vendor = ""
            if "(" in rest and ")" in rest:
                vendor = rest[rest.index("(") + 1 : rest.rindex(")")]
            current["mac"] = mac
            current["vendor"] = vendor
    return hosts


def _run_nmap(subnet: str, timeout: float) -> list[dict] | None:
    """nmap si existe en PATH; None si no (para caer al ping-sweep)."""
    if not shutil.which("nmap"):
        return None
    try:
        proc = subprocess.run(
            ["nmap", "-sn", "-oG", "-", subnet],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_nmap_grepable(proc.stdout)


def _ping(ip: str, timeout: float) -> bool:
    """Un ping por host; Windows usa ``-n/-w``, el resto ``-c/-W``."""
    import sys

    if sys.platform == "win32":
        cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(int(timeout)), ip]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _ping_sweep(subnet: str, timeout: float) -> list[dict]:
    """Sweep stdlib: paraleliza pings (max 1024 hosts por seguridad)."""
    network = ipaddress.ip_network(subnet, strict=False)
    hosts = list(network.hosts())
    if len(hosts) > MAX_SCAN_HOSTS:
        raise ValueError(
            f"Subred {subnet} demasiado grande ({len(hosts)} hosts > {MAX_SCAN_HOSTS}); "
            "usa una subred mas concreta (IOT_SCAN_SUBNET)"
        )
    found: list[dict] = []
    with ThreadPoolExecutor(max_workers=64) as pool:
        for ip, up in zip(hosts, pool.map(lambda h: _ping(str(h), timeout), hosts), strict=False):
            if up:
                found.append({"ip": str(ip), "status": "up", "mac": "", "vendor": ""})
    return found


def _ha_hosts() -> list[dict]:
    """Hosts con IP en atributos de dispositivos ya cacheados por HA."""
    try:
        from iot_hub.service import get_service

        devices = get_service().get_devices()
    except Exception:
        return []
    hosts: list[dict] = []
    for dev in devices:
        attrs = dev.get("attributes") or {}
        ip = attrs.get("ip") or attrs.get("ip_address") or attrs.get("host")
        if ip:
            hosts.append({"ip": str(ip), "status": "up", "mac": "", "vendor": "", "fuente": "ha"})
    return hosts


def scan(subnet: str | None = None, out_file=None) -> dict:
    """Escanea la subred, fusiona fuentes y escribe el inventario."""
    subnet = subnet or config.IOT_SCAN_SUBNET
    out_file = out_file or config.INVENTORY_FILE
    started = time.time()

    nmap_hosts = _run_nmap(subnet, config.IOT_SCAN_TIMEOUT)
    method = "nmap"
    if nmap_hosts is None:
        nmap_hosts = _ping_sweep(subnet, config.IOT_SCAN_TIMEOUT)
        method = "ping"

    # Fusion por IP: nmap/ping aporta mac/vendor, HA aporta entidad conocida
    by_ip: dict[str, dict] = {}
    for host in nmap_hosts:
        host = dict(host)
        host.setdefault("fuente", method)
        host["last_seen"] = time.time()
        by_ip[host["ip"]] = host
    for host in _ha_hosts():
        ip = host["ip"]
        if ip in by_ip:
            by_ip[ip]["ha_entity"] = True
        else:
            host["last_seen"] = time.time()
            by_ip[ip] = host

    inventory = {
        "subnet": subnet,
        "method": method,
        "scanned_at": time.time(),
        "scan_seconds": round(time.time() - started, 2),
        "host_count": len(by_ip),
        "hosts": sorted(by_ip.values(), key=lambda h: ipaddress.ip_address(h["ip"])),
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    return inventory


def load_inventory(out_file=None) -> dict:
    """Lee el inventario persistido (o uno vacio)."""
    out_file = out_file or config.INVENTORY_FILE
    try:
        return json.loads(out_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"subnet": "", "method": "", "scanned_at": 0.0, "host_count": 0, "hosts": []}

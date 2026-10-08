"""Auditor LAN/WiFi: quién hay en tu red y qué expone.

Ping-sweep (stdlib, sin nmap) + sonda TCP a puertos típicos + diff contra
`data/secops/known_devices.json`. Un dispositivo nuevo en tu WiFi es el
hallazgo más importante de todos: puede ser un intruso.
"""
from __future__ import annotations

import concurrent.futures
import ipaddress
import json
import os
import subprocess
import sys

from secops.models import Finding
from secops.net import tcp_abierto

KNOWN_FILE = os.path.join("data", "secops", "known_devices.json")

# Puertos que delatan servicios: (puerto, descripción)
PUERTOS_SONDA = [
    (22, "ssh"), (23, "telnet"), (80, "http"), (443, "https"),
    (445, "smb"), (554, "rtsp/cámara"), (5555, "adb"), (8000, "http-alt"),
    (8080, "http-alt"), (8081, "http-alt"), (8082, "daniela-gw"),
    (8095, "daniela-pwa"), (8443, "https-alt"), (9200, "daniela"),
    (9300, "hermes"), (9997, "dashboard"),
]


def _ping(ip: str, timeout_ms: int = 700) -> bool:
    if sys.platform == "win32":
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), ip]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=(timeout_ms / 1000) + 2)
        return r.returncode == 0
    except Exception:
        return False


def sweep(subnet: str = "192.168.1.0/24") -> list[str]:
    red = ipaddress.ip_network(subnet, strict=False)
    if red.num_addresses > 1024:
        raise ValueError("subred demasiado grande (máx /22)")
    ips = [str(h) for h in red.hosts()]
    vivos = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ex:
        fut = {ex.submit(_ping, ip): ip for ip in ips}
        for f in concurrent.futures.as_completed(fut):
            try:
                if f.result():
                    vivos.append(fut[f])
            except Exception:
                continue
    return sorted(vivos, key=lambda ip: tuple(int(p) for p in ip.split(".")))


def sondear_puertos(ip: str, puertos: list[tuple[int, str]] | None = None) -> list[dict]:
    puertos = puertos or PUERTOS_SONDA
    abiertos = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        fut = {ex.submit(tcp_abierto, ip, p, 1.0): (p, d) for p, d in puertos}
        for f in concurrent.futures.as_completed(fut):
            try:
                if f.result():
                    p, d = fut[f]
                    abiertos.append({"puerto": p, "servicio": d})
            except Exception:
                continue
    return sorted(abiertos, key=lambda x: x["puerto"])


def cargar_conocidos(ruta: str = KNOWN_FILE) -> dict:
    try:
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def guardar_conocidos(dispositivos: dict, ruta: str = KNOWN_FILE) -> None:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(dispositivos, fh, indent=2, ensure_ascii=False, sort_keys=True)


def auditar_lan(subnet: str = "192.168.1.0/24", barrer=sweep, sondear=sondear_puertos) -> list[Finding]:
    hallazgos = []
    try:
        vivos = barrer(subnet)
    except Exception as e:
        return [
            Finding(
                id="lan-sweep-fallo",
                titulo="No se pudo barrer la LAN",
                severidad="media",
                donde=subnet,
                evidencia=str(e)[:120],
                auditor="lan",
            )
        ]
    conocidos = cargar_conocidos()
    hallazgos.append(
        Finding(
            id="lan-inventario",
            titulo=f"LAN {subnet}: {len(vivos)} dispositivos activos",
            severidad="info",
            donde=subnet,
            evidencia=", ".join(vivos[:20]),
            auditor="lan",
        )
    )
    nuevos = [ip for ip in vivos if ip not in conocidos]
    for ip in nuevos:
        hallazgos.append(
            Finding(
                id=f"lan-nuevo-{ip.replace('.', '-')}",
                titulo=f"Dispositivo NUEVO en tu WiFi: {ip}",
                severidad="alta",
                donde=ip,
                evidencia="no está en known_devices.json",
                remedio="Si lo reconoces, añádelo a conocidos; si no, "
                "cambia la clave WiFi y revisa el router.",
                auditor="lan",
            )
        )
    for ip in vivos:
        for s in sondear(ip):
            sev = "critica" if s["puerto"] in (23, 445, 5555) else "media"
            hallazgos.append(
                Finding(
                    id=f"lan-puerto-{ip.replace('.', '-')}-{s['puerto']}",
                    titulo=f"{ip}:{s['puerto']} abierto ({s['servicio']})",
                    severidad=sev if ip not in conocidos else "baja",
                    donde=f"{ip}:{s['puerto']}",
                    evidencia=f"TCP connect OK a {s['servicio']}",
                    remedio="Cerrar lo innecesario; ADB (5555) y telnet (23) "
                    "jamás en WiFi.",
                    auditor="lan",
                )
            )
    return hallazgos

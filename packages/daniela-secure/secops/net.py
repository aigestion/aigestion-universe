"""Transporte stdlib para los auditores: HTTP + TCP + netstat.

Todo inyectable para tests (nadie toca la red en `tests/`).
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class HttpResp:
    status: int
    headers: dict
    body: bytes
    url: str


def http_get(url: str, timeout: float = 4.0, headers: dict | None = None) -> HttpResp:
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return HttpResp(r.status, dict(r.headers), r.read(65536), url)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(65536)
        except Exception:
            body = b""
        return HttpResp(e.code, dict(e.headers or {}), body, url)
    except Exception as e:
        raise ConnectionError(f"{url}: {e}") from e


def http_post_json(url: str, payload: dict, timeout: float = 6.0) -> HttpResp:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return HttpResp(r.status, dict(r.headers), r.read(65536), url)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(65536)
        except Exception:
            body = b""
        return HttpResp(e.code, dict(e.headers or {}), body, url)
    except Exception as e:
        raise ConnectionError(f"{url}: {e}") from e


def tcp_abierto(host: str, port: int, timeout: float = 1.5) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def banner_http(host: str, port: int, timeout: float = 4.0) -> HttpResp | None:
    """GET / y /api/health sin auth. None si no hay HTTP."""
    for path in ("/", "/api/health", "/api/status"):
        try:
            r = http_get(f"http://{host}:{port}{path}", timeout=timeout)
            if r.status < 500:
                return r
        except ConnectionError:
            continue
    return None


def netstat_listen() -> list[dict]:
    """Sockets TCP en LISTEN: [{ip, puerto}]. Windows (netstat) y Linux (ss)."""
    filas: list[dict] = []
    try:
        out = subprocess.run(
            ["netstat", "-an", "-p", "TCP"], capture_output=True, text=True, timeout=15
        ).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            out = subprocess.run(
                ["ss", "-ltn"], capture_output=True, text=True, timeout=15
            ).stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []
    for linea in out.splitlines():
        m = re.search(r"(LISTEN|LISTENING)\s*$", linea)
        if not m:
            continue
        partes = linea.split()
        # netstat: Proto Local Address ... State | ss: State Recv-Q ... Local Address:Port
        for tok in partes:
            mm = re.match(r"(\[?[\d.*a-fA-F:]+\]?):(\d+)$", tok)
            if mm:
                filas.append({"ip": mm.group(1).strip("[]"), "puerto": int(mm.group(2))})
                break
    vistos = set()
    unicos = []
    for f in filas:
        k = (f["ip"], f["puerto"])
        if k not in vistos:
            vistos.add(k)
            unicos.append(f)
    return unicos


def es_wildcard(ip: str) -> bool:
    return ip in ("0.0.0.0", "*", "::", "::/0", "0.0.0.0/0")

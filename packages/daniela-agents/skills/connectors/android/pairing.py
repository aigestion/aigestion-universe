#!/usr/bin/env python3
"""Pairing PC <-> Pixel por challenge-response (sin exponer el token).

El problema: PC y gateway comparten `PIXEL_TOKEN`/`PIXEL_GATEWAY_TOKEN`,
pero nada prueba que ambos extremos tengan el MISMO valor hasta que algo
falla con 401s confusos. Este modulo lo prueba con criptografia:

  PC: nonce aleatorio -> POST /api/pair/challenge -> HMAC(token, nonce)
  PC compara con su propio HMAC. Coincide => paired. Nunca viaja el token.

El resultado se guarda en `.paired.json` (SOLO fingerprint sha256 del
token + ip + fecha, jamas el token) para que el hub sepa con quien hablo
por ultima vez. Ver frontend/apps/android-app/mobile-app/api/termux_api_gateway.py::pair_challenge (lado telefono).

Uso:
    python skills/connectors/android/pairing.py 192.168.1.170 [--port 8082]
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / ".paired.json"
DEFAULT_PORT = 8082


def _repo_env() -> dict:
    """Lee .env de la raiz del repo (el pairing se lanza a mano, sin dotenv)."""
    datos: dict = {}
    raiz = Path(__file__).resolve().parent.parent / ".env"
    if raiz.is_file():
        for linea in raiz.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.strip().split("=", 1)
                datos.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return datos


def _token() -> str:
    token = os.getenv("PIXEL_TOKEN", "") or os.getenv("PIXEL_GATEWAY_TOKEN", "")
    if not token:
        token = _repo_env().get("PIXEL_TOKEN", "") or _repo_env().get("PIXEL_GATEWAY_TOKEN", "")
    if not token:
        raise SystemExit("sin PIXEL_TOKEN: exportalo o rellena el .env de la raiz")
    return token


def challenge(ip: str, port: int = DEFAULT_PORT, timeout: int = 8) -> dict:
    """Ejecuta el challenge contra el gateway. Devuelve dict con ok/error."""
    token = _token()
    nonce = secrets.token_hex(16)
    url = f"http://{ip}:{port}/api/pair/challenge"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"nonce": nonce}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:  # red, telefono apagado, gateway caido...
        return {"ok": False, "ip": ip, "error": f"sin respuesta: {exc}"}
    esperado = hmac.new(token.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    if not data.get("hmac") or not hmac.compare_digest(data["hmac"], esperado):
        return {"ok": False, "ip": ip, "error": "HMAC no coincide: tokens distintos"}
    registro = {
        "ip": ip,
        "port": port,
        "paired_at": datetime.now().isoformat(timespec="seconds"),
        "token_fingerprint": hashlib.sha256(token.encode()).hexdigest()[:16],
    }
    STATE_FILE.write_text(json.dumps(registro, indent=2), encoding="utf-8")
    return {"ok": True, **registro}


def main(argv: list[str] | None = None) -> int:
    args = (argv or sys.argv[1:])
    if not args or args in (["-h"], ["--help"]):
        print("uso: python skills/connectors/android/pairing.py <ip> [--port N]")
        return 2
    ip = args[0]
    port = int(args[args.index("--port") + 1]) if "--port" in args else DEFAULT_PORT
    resultado = challenge(ip, port)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

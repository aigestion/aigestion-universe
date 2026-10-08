"""Auditor de secretos: reutiliza las reglas del secret-guard sobre el árbol.

No duplica reglas: importa `scan_text` de scripts/utils/secret_guard.py y
lo aplica a los ficheros rastreados por git (lo mismo que se podría subir).
"""
from __future__ import annotations

import os
import subprocess
import sys

from secops.models import Finding

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_UTILS = os.path.join(_RAIZ, "scripts", "utils")
if _UTILS not in sys.path:
    sys.path.insert(0, _UTILS)

EXTS = (".py", ".js", ".ts", ".json", ".yml", ".yaml", ".toml", ".md", ".txt", ".env")
MAX_BYTES = 1_000_000


def _ficheros() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, timeout=30, cwd=_RAIZ
        ).stdout
        return [l.strip() for l in out.splitlines() if l.strip().endswith(EXTS)]
    except Exception:
        return []


def auditar_secretos() -> list[Finding]:
    try:
        from secret_guard import scan_text
    except Exception as e:
        return [
            Finding(
                id="secretos-guard-no-importable",
                titulo="secret_guard no importable",
                severidad="media",
                donde="scripts/utils/secret_guard.py",
                evidencia=str(e),
                remedio="Restaurar el módulo: sin él no hay segunda red.",
                auditor="secretos",
            )
        ]
    hallazgos = []
    for rel in _ficheros():
        ruta = os.path.join(_RAIZ, rel)
        try:
            if os.path.getsize(ruta) > MAX_BYTES:
                continue
            with open(ruta, encoding="utf-8", errors="ignore") as f:
                texto = f.read()
        except OSError:
            continue
        try:
            for h in scan_text(rel, texto):
                sev = getattr(h, "severity", "alta") or "alta"
                if sev not in ("critica", "alta", "media", "baja", "info"):
                    sev = "alta"
                hallazgos.append(
                    Finding(
                        id=f"secretos-{rel}-{getattr(h, 'line', 0)}",
                        titulo=f"Posible secreto: {getattr(h, 'rule', 'regla')}",
                        severidad=sev,
                        donde=f"{rel}:{getattr(h, 'line', '?')}",
                        evidencia=str(getattr(h, "match", "") or "")[:80],
                        remedio="Rotar la credencial, moverla a .env (ignorado) "
                        "y reescribir el historial si ya se subió.",
                        auditor="secretos",
                    )
                )
        except Exception:
            continue
    return hallazgos

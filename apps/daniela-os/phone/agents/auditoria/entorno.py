"""Auditoría de entorno Windows para Daniela.

Daniela observa cómo trabaja el usuario y aconseja mejoras:
  1. Estado del sistema (disco, memoria, procesos)
  2. Salud del proyecto (git status, tests, ruff)
  3. Recomendaciones de mejora

El resultado se reporta al cerebro de Daniela y se guarda para
que el usuario pueda ver el historial de auditorías.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_DIR = Path(__file__).resolve().parent
_RAIZ = _DIR.parent.parent.parent

_AUDITORIAS: list[dict[str, Any]] = []


def _raiz() -> Path:
    return _RAIZ


def _estado_disco() -> dict[str, Any]:
    """Espacio en disco del drive del proyecto."""
    try:
        usage = shutil.disk_usage(str(_raiz()))
        total_gb = usage.total / (1024**3)
        libre_gb = usage.free / (1024**3)
        usado_pct = round((usage.used / usage.total) * 100, 1)
        return {
            "total_gb": round(total_gb, 1),
            "libre_gb": round(libre_gb, 1),
            "usado_pct": usado_pct,
            "alerta": usado_pct > 85,
        }
    except Exception as e:
        return {"error": str(e)}


def _estado_memoria() -> dict[str, Any]:
    """Uso de memoria RAM (psutil si está, si no skip)."""
    try:
        import psutil

        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 1),
            "usada_gb": round(mem.used / (1024**3), 1),
            "usado_pct": mem.percent,
            "alerta": mem.percent > 85,
        }
    except ImportError:
        return {"info": "psutil no instalado, sin datos de RAM"}


def _estado_procesos() -> dict[str, Any]:
    """Procesos Python activos (señal de que hay agentes corriendo)."""
    try:
        import psutil

        procs = []
        for p in psutil.process_iter(["name", "cpu_percent", "memory_info"]):
            try:
                if "python" in (p.info["name"] or "").lower():
                    procs.append(
                        {
                            "pid": p.pid,
                            "nombre": p.info["name"],
                            "cpu_pct": round(p.info["cpu_percent"], 1),
                            "mem_mb": round(p.info["memory_info"].rss / (1024**2), 1)
                            if p.info["memory_info"]
                            else 0,
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"python_activos": len(procs), "procesos": procs[:10]}
    except ImportError:
        return {"info": "psutil no instalado"}


def _salud_proyecto() -> dict[str, Any]:
    """Git status + tests + ruff en un vistazo."""
    raiz = _raiz()
    resultado: dict[str, Any] = {}

    try:
        git_status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(raiz),
        )
        lineas = [l for l in git_status.stdout.strip().split("\n") if l]
        resultado["git"] = {
            "archivos_cambiados": len(lineas),
            "alerta": len(lineas) > 50,
        }
    except Exception as e:
        resultado["git"] = {"error": str(e)}

    try:
        ruff = subprocess.run(
            [sys.executable, "-m", "ruff", "check", ".", "--statistics"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(raiz),
        )
        if ruff.returncode == 0:
            resultado["ruff"] = {"ok": True, "errores": 0}
        else:
            ultimo = ruff.stdout.strip().split("\n")[-1] if ruff.stdout else ""
            resultado["ruff"] = {"ok": False, "detalle": ultimo[:120]}
    except Exception as e:
        resultado["ruff"] = {"error": str(e)}

    return resultado


def _recomendaciones(estado: dict[str, Any]) -> list[dict[str, Any]]:
    """Genera recomendaciones basadas en el estado observado."""
    recs: list[dict[str, Any]] = []

    disco = estado.get("disco", {})
    if disco.get("alerta"):
        recs.append(
            {
                "tipo": "disco",
                "severidad": "alta",
                "mensaje": f"Disco al {disco['usado_pct']}%. "
                f"Limpia tmp, caches o archivos grandes.",
            }
        )

    mem = estado.get("memoria", {})
    if mem.get("alerta"):
        recs.append(
            {
                "tipo": "memoria",
                "severidad": "alta",
                "mensaje": f"RAM al {mem['usado_pct']}%. "
                f"Cierra procesos innecesarios o divide el trabajo.",
            }
        )

    git = estado.get("salud", {}).get("git", {})
    if git.get("alerta"):
        recs.append(
            {
                "tipo": "git",
                "severidad": "media",
                "mensaje": f"{git['archivos_cambiados']} archivos sin commitear. "
                f"Considera hacer commit parcial para no perder trabajo.",
            }
        )

    ruff = estado.get("salud", {}).get("ruff", {})
    if not ruff.get("ok") and not ruff.get("error"):
        recs.append(
            {
                "tipo": "lint",
                "severidad": "baja",
                "mensaje": f"Ruff reporta problemas: {ruff.get('detalle', '')}",
            }
        )

    procs = estado.get("procesos", {})
    if procs.get("python_activos", 0) > 10:
        recs.append(
            {
                "tipo": "procesos",
                "severidad": "baja",
                "mensaje": f"{procs['python_activos']} procesos Python activos. "
                f"Verifica que no haya zombies de tests o agentes.",
            }
        )

    if not recs:
        recs.append(
            {
                "tipo": "ok",
                "severidad": "info",
                "mensaje": "Entorno sano. Sin acciones urgentes.",
            }
        )
    return recs


def auditar(slug: str = "") -> dict[str, Any]:
    """Ejecuta la auditoría completa del entorno.

    Recopila:
      - Estado de disco
      - Estado de memoria
      - Procesos Python activos
      - Salud del proyecto (git + ruff)

    Genera recomendaciones y, si `slug` se da, reporta al cerebro.
    """
    estado = {
        "disco": _estado_disco(),
        "memoria": _estado_memoria(),
        "procesos": _estado_procesos(),
        "salud": _salud_proyecto(),
        "sistema": {
            "os": platform.system(),
            "release": platform.release(),
            "python": sys.version.split()[0],
        },
        "ts": time.time(),
    }

    recomendaciones = _recomendaciones(estado)
    estado["recomendaciones"] = recomendaciones

    _AUDITORIAS.append(estado)

    if slug:
        try:
            from phone.agents.brain import get_brain

            brain = get_brain()
            hay_alertas = any(r["severidad"] == "alta" for r in recomendaciones)
            brain.report(
                agente="auditoria-entorno",
                resultado={
                    "success": True,
                    "output": f"{len(recomendaciones)} recomendaciones",
                    "alertas": sum(1 for r in recomendaciones if r["severidad"] == "alta"),
                },
                prioridad="alta" if hay_alertas else "normal",
            )
        except Exception:
            pass

    return estado


def historial(limit: int = 10) -> list[dict[str, Any]]:
    """Últimas auditorías en memoria."""
    return _AUDITORIAS[-limit:]


def resumen_texto(aud: dict[str, Any]) -> str:
    """Resumen legible de una auditoría para el chat de Daniela."""
    lineas = [f"Auditoría {platform.system()} {aud.get('ts', '')}"]
    for rec in aud.get("recomendaciones", []):
        icono = {"alta": "[!]", "media": "[~]", "baja": "[.]", "info": "[ok]"}.get(
            rec["severidad"], "[?]"
        )
        lineas.append(f"  {icono} {rec['mensaje']}")
    return "\n".join(lineas)

"""Sandbox de validación pre-integración para Daniela.

Antes de integrar (merge) código nuevo, Daniela lo valida en este sandbox:
  1. Compilar (syntax check)
  2. Importar sin errores
  3. Ejecutar tests básicos
  4. Verificar que no rompe el gate existente

El resultado se reporta al cerebro de Daniela (jerarquía: sandbox → Daniela).
Daniela + usuario deciden si aprobar o rechazar la integración.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_DIR = Path(__file__).resolve().parent
_RAIZ = _DIR.parent.parent.parent

_RESULTADOS: list[dict[str, Any]] = []


def _raiz() -> Path:
    return _RAIZ


def _comprobar_sintaxis(ruta: str) -> dict[str, Any]:
    """Compila el fichero sin ejecutarlo (ast.parse)."""
    import ast

    try:
        codigo = Path(ruta).read_text(encoding="utf-8")
        ast.parse(codigo, filename=ruta)
        return {"ok": True, "mensaje": "sintaxis correcta"}
    except SyntaxError as e:
        return {"ok": False, "mensaje": f"error sintaxis línea {e.lineno}: {e.msg}"}
    except Exception as e:
        return {"ok": False, "mensaje": str(e)}


def _comprobar_imports(ruta: str) -> dict[str, Any]:
    """Intenta importar el módulo sin ejecutar efectos secundarios graves."""
    nombre = Path(ruta).stem
    carpeta = str(Path(ruta).parent)
    try:
        resultado = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, {carpeta!r});"
                f"import importlib; m = importlib.import_module('{nombre}')",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(_raiz()),
        )
        if resultado.returncode == 0:
            return {"ok": True, "mensaje": f"import {nombre} OK"}
        return {"ok": False, "mensaje": f"import falló: {resultado.stderr[:200]}"}
    except Exception as e:
        return {"ok": False, "mensaje": str(e)}


def _comprobar_tests(ruta: str) -> dict[str, Any]:
    """Ejecuta los tests relacionados con el módulo (si existen)."""
    nombre = Path(ruta).stem
    carpeta_tests = _raiz() / "tests"
    candidatos = list(carpeta_tests.rglob(f"test_{nombre}.py"))
    if not candidatos:
        return {"ok": True, "mensaje": f"no hay tests para {nombre}"}
    try:
        resultado = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(candidatos[0]),
                "-q",
                "--tb=no",
                "-p",
                "no:cacheprovider",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(_raiz()),
        )
        if resultado.returncode == 0:
            return {"ok": True, "mensaje": f"tests de {nombre} pasan"}
        return {"ok": False, "mensaje": f"tests fallan: {resultado.stdout[:200]}"}
    except Exception as e:
        return {"ok": False, "mensaje": str(e)}


def _comprobar_ruff(ruta: str) -> dict[str, Any]:
    """Verifica que el código cumple el estilo (ruff)."""
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "ruff", "check", ruta, "--select", "E,F"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(_raiz()),
        )
        if resultado.returncode == 0:
            return {"ok": True, "mensaje": "ruff OK"}
        return {"ok": False, "mensaje": f"ruff: {resultado.stdout[:200]}"}
    except Exception as e:
        return {"ok": False, "mensaje": str(e)}


def validar_pre_integracion(ruta: str, slug: str = "") -> dict[str, Any]:
    """Valida un módulo antes de integrarlo.

    Ejecuta una batería de comprobaciones:
      1. Sintaxis (ast.parse)
      2. Imports (importlib)
      3. Tests (pytest si existen)
      4. Estilo (ruff)

    Devuelve:
      {
        "ok": bool,
        "ruta": str,
        "comprobaciones": [...],
        "resumen": str,
        "ts": float
      }

    Si `slug` se da, el resultado se reporta al cerebro de Daniela.
    """
    comprobaciones: list[dict[str, Any]] = []
    ruta_abs = str(Path(ruta).resolve())

    comprobaciones.append({"tipo": "sintaxis", **_comprobar_sintaxis(ruta_abs)})
    comprobaciones.append({"tipo": "imports", **_comprobar_imports(ruta_abs)})
    comprobaciones.append({"tipo": "tests", **_comprobar_tests(ruta_abs)})
    comprobaciones.append({"tipo": "estilo", **_comprobar_ruff(ruta_abs)})

    todos_ok = all(c["ok"] for c in comprobaciones)
    fallidos = [c for c in comprobaciones if not c["ok"]]
    resumen = (
        f"{len(comprobaciones) - len(fallidos)}/{len(comprobaciones)} comprobaciones OK"
        if todos_ok
        else f"{len(fallidos)} comprobaciones fallidas: "
        + "; ".join(f"{c['tipo']}: {c['mensaje'][:60]}" for c in fallidos)
    )

    resultado = {
        "ok": todos_ok,
        "ruta": ruta_abs,
        "comprobaciones": comprobaciones,
        "resumen": resumen,
        "ts": time.time(),
    }

    _RESULTADOS.append(resultado)

    if slug:
        try:
            from phone.agents.brain import get_brain

            brain = get_brain()
            prioridad = "alta" if not todos_ok else "normal"
            brain.report(
                agente="sandbox-pre-integracion",
                resultado={
                    "success": todos_ok,
                    "output": resumen,
                    "ruta": ruta_abs,
                    "comprobaciones": comprobaciones,
                },
                prioridad=prioridad,
            )
        except Exception:
            pass

    return resultado


def historial(limit: int = 20) -> list[dict[str, Any]]:
    """Últimos resultados de validación en memoria."""
    return _RESULTADOS[-limit:]


def pending_decisions(slug: str = "") -> list[dict[str, Any]]:
    """Validaciones pendientes de decisión (fallos)."""
    if not slug:
        return [r for r in _RESULTADOS if not r["ok"]]
    try:
        from phone.agents.brain import get_brain

        brain = get_brain()
        return brain.reportes_pendientes()
    except Exception:
        return [r for r in _RESULTADOS if not r["ok"]]

#!/usr/bin/env python3
# Migrated from aig/core/safe_exec.py (legacy) — preserved as-is, see MIGRATION_PLAN.md.
"""
Safe Exec — Ejecucion segura de comandos (E-02 / Fase 5)
=========================================================
Reemplazo directo de os.system() y os.popen(). Nunca usa shell.

Regla del proyecto: NADA de os.system(), NADA de shell=True.
Este modulo es el punto unico de ejecucion de comandos externos.

Uso:
    from safe_exec import run_cmd, run_code, run_out

    run_cmd("termux-torch on")            # -> CompletedProcess
    run_code("termux-torch on")           # -> int (como os.system)
    run_out("termux-battery-status")      # -> str (como os.popen().read())

Por que es seguro:
    - shlex.split() respeta las comillas: termux-tts-speak 'hola mundo'
      se convierte en ['termux-tts-speak', 'hola mundo'], no en 3 argumentos.
    - No hay shell intermedio -> no hay inyeccion posible.
    - Timeout por defecto -> un comando colgado no bloquea Daniela.

Coste: $0 — Python stdlib.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from collections.abc import Sequence

DEFAULT_TIMEOUT = 10

CmdArg = str | Sequence[str]


def _expand(arg: str) -> str:
    """Expande ~ y variables de entorno, como haria el shell."""
    if arg.startswith("~"):
        arg = os.path.expanduser(arg)
    if "$" in arg:
        arg = os.path.expandvars(arg)
    return arg


def _to_args(cmd: CmdArg) -> list[str]:
    """Convierte el comando a lista de argumentos sin pasar por el shell."""
    if isinstance(cmd, str):
        parts = shlex.split(cmd)
    else:
        parts = [str(c) for c in cmd]
    return [_expand(p) for p in parts]


def run_cmd(cmd: CmdArg, timeout: int = DEFAULT_TIMEOUT, check: bool = False,
            cwd: str | None = None):
    """Ejecuta un comando sin shell. Devuelve CompletedProcess.

    Args:
        cmd: string con el comando, o lista de argumentos (preferido).
        timeout: segundos antes de abortar.
        check: si True, lanza CalledProcessError cuando el codigo != 0.
        cwd: directorio de trabajo (None = CWD del proceso padre).

    Returns:
        subprocess.CompletedProcess con .returncode, .stdout, .stderr.
        Si el binario no existe -> FileNotFoundError capturado, returncode 127.
    """
    args = _to_args(cmd)
    if not args:
        return subprocess.CompletedProcess(args=[], returncode=1,
                                           stdout="", stderr="comando vacio")
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            check=check,
            cwd=cwd,
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=args, returncode=127, stdout="",
            stderr=f"comando no encontrado: {args[0]}")
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=args, returncode=124, stdout="",
            stderr=f"timeout tras {timeout}s")
    except Exception as e:                      # permisos, OSError, etc.
        return subprocess.CompletedProcess(
            args=args, returncode=1, stdout="", stderr=str(e))


def run_bg(cmd: CmdArg) -> subprocess.Popen:
    """Lanza un proceso en segundo plano de manera segura sin shell.
    Equivalente seguro de 'comando &' o nohup en background.
    """
    args = _to_args(cmd)
    if not args:
        raise ValueError("Comando vacío")
    return subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True if os.name != "nt" else False
    )


def run_code(cmd: CmdArg, timeout: int = DEFAULT_TIMEOUT) -> int:
    """Como os.system(): devuelve solo el codigo de salida."""
    return run_cmd(cmd, timeout=timeout).returncode


def run_out(cmd: CmdArg, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Como os.popen(cmd).read(): devuelve solo la salida."""
    return run_cmd(cmd, timeout=timeout).stdout


def run_json(cmd: CmdArg, timeout: int = DEFAULT_TIMEOUT):
    """Ejecuta y parsea la salida como JSON. Devuelve None si no es JSON."""
    import json
    out = run_out(cmd, timeout=timeout).strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def ok(cmd: CmdArg, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """True si el comando salio con codigo 0."""
    return run_code(cmd, timeout=timeout) == 0


if __name__ == "__main__":
    print("Safe Exec — prueba rapida")
    r = run_cmd("python --version")
    print(f"  returncode={r.returncode}  stdout={r.stdout.strip()}")
    print(f"  run_code -> {run_code('python --version')}")
    print("  shlex respeta comillas:",
          _to_args("termux-tts-speak 'hola mundo'"))

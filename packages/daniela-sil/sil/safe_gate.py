#!/usr/bin/env python3
"""Safe Evolution Gate (Fase 3, idea #9) — main solo se toca en verde.

Regla: todo cambio de autofix/SIL pasa por rama + gate (los trabajos
cerrados de `ci_runner`: sintaxis, seguridad, ruff en quick; +arranque,
mypy, pytest en full) antes de fusionar a main.

- `evaluar_gate(nivel)`: corre el gate sobre el checkout actual.
  Nunca lanza: devuelve {"ok", "resultados", "resumen"}.
- `fusionar_si_verde(rama)`: checkout rama → gate → checkout main →
  merge --no-ff. Cualquier fallo aborta SIN fusionar (honesto).
- El hook `githooks/pre-push` ejecuta el nivel quick (segundos).

CLI: python safe_gate.py check [--full] | fusionar <rama>
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

GATE_QUICK = ["sintaxis", "seguridad", "ruff"]
GATE_FULL = ["sintaxis", "seguridad", "ruff", "arranque", "mypy", "pytest"]


def _git(*args: str, timeout: int = 60):
    """git sin shell. Devuelve (rc, stdout). Nunca lanza."""
    try:
        from bridges.comms.safe_exec import run_cmd
    except ImportError:
        import subprocess

        try:
            r = subprocess.run(["git", *args], capture_output=True, text=True,
                               errors="replace", timeout=timeout, cwd=str(REPO_ROOT))
            return r.returncode, (r.stdout or "").strip()
        except Exception as e:
            return 1, str(e)[:200]
    r = run_cmd(["git", *args], timeout=timeout)
    return r.returncode, ((r.stdout or "").strip())


def rama_actual() -> str:
    """Rama checkout ahora ("" si falla)."""
    rc, out = _git("rev-parse", "--abbrev-ref", "HEAD")
    return out if rc == 0 else ""


def arbol_limpio() -> bool:
    """Sin cambios versionados pendientes (los untracked no bloquean;
    si un checkout los pisara, su propio rc lo delata)."""
    rc, out = _git("status", "--porcelain", "--untracked-files=no")
    return rc == 0 and out == ""


def evaluar_gate(nivel: str = "quick") -> dict[str, Any]:
    """Corre los trabajos del gate. Nunca lanza excepcion."""
    trabajos = GATE_FULL if nivel == "full" else GATE_QUICK
    t0 = time.time()
    try:
        from core.ci.ci_runner import get_instance

        r = get_instance().ejecutar(trabajos)
        fallidos = list(r.get("fallidos", []) or [])
        return {
            "ok": bool(r.get("ok")), "nivel": nivel,
            "duracion_s": round(time.time() - t0, 1),
            "fallidos": fallidos,
            "detalle": {k: {"ok": v.get("ok"),
                            "detalle": str(v.get("detalle", ""))[:300]}
                        for k, v in (r.get("trabajos") or {}).items()},
        }
    except Exception as e:
        return {"ok": False, "nivel": nivel, "fallidos": ["gate"],
                "detalle": {}, "error": str(e)[:300]}


def fusionar_si_verde(rama: str, nivel: str = "full") -> dict[str, Any]:
    """Fusiona rama a main SOLO con gate verde. Pasos reversibles."""
    if not (rama or "").strip() or rama in ("main", "master"):
        return {"ok": False, "error": "rama invalida (ni vacia ni main)"}
    origen = rama_actual()
    if not arbol_limpio():
        return {"ok": False, "error": "arbol sucio: commitea o guarda antes"}
    rc, _ = _git("checkout", rama)
    if rc != 0:
        return {"ok": False, "error": f"no se pudo checkout {rama} (arbol?)"}
    gate = evaluar_gate(nivel)
    if not gate["ok"]:
        rc2, _ = _git("checkout", origen or "main")
        if rc2 != 0:
            return {"ok": False, "error": "gate en rojo Y no se pudo volver a "
                    f"{origen or 'main'}: revisa 'git status'",
                    "fallidos": gate["fallidos"], "rama": rama}
        return {"ok": False, "error": "gate en rojo: no se fusiona",
                "fallidos": gate["fallidos"], "rama": rama}
    rc, _ = _git("checkout", "main")
    if rc != 0:
        _git("checkout", origen or "main")
        return {"ok": False, "error": "no se pudo checkout main: nada fusionado"}
    rc, out = _git("merge", "--no-ff", rama, "-m", f"merge(gate): {rama} en verde")
    if rc != 0:
        _git("merge", "--abort")
        _git("checkout", origen or "main")
        return {"ok": False, "error": f"merge fallo (conflicto?): {out[:200]}"}
    return {"ok": True, "rama": rama, "gate": gate["duracion_s"]}


# ── CLI ──────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe Evolution Gate")
    sub = parser.add_subparsers(dest="cmd")

    p_c = sub.add_parser("check", help="Evaluar gate del checkout actual")
    p_c.add_argument("--full", action="store_true")

    p_f = sub.add_parser("fusionar", help="Fusionar rama a main si gate verde")
    p_f.add_argument("rama")
    p_f.add_argument("--quick", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "check":
        import json

        r = evaluar_gate("full" if args.full else "quick")
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r["ok"] else 1
    if args.cmd == "fusionar":
        import json

        r = fusionar_si_verde(args.rama, "quick" if args.quick else "full")
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r["ok"] else 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

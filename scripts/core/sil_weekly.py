#!/usr/bin/env python3
"""Job semanal SIL (Fase 3 extendida) — self-improvement como rutina, no clases.

Por defecto SOLO pasos locales (sin efectos externos):
  review -> lessons-export -> dashboard -> scoreboard snapshot
Con --full anade dispatch + verify (abren PRs via Jules: requiere claves
y aceptas el riesgo; ver docs/SIL-WEEKLY-JOB.md).

Uso:
  python scripts/sil_weekly.py            # local, seguro
  python scripts/sil_weekly.py --full     # loop completo (dispatch incluido)
  python scripts/sil_weekly.py --check    # que correria, sin ejecutar

Escribe data/sil/weekly_report_<fecha>.json. Nunca lanza excepcion:
sale 0 si los pasos locales van bien, 1 si algo fallo.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

try:
    from safe_exec import run_cmd
except ImportError:
    run_cmd = None  # type: ignore

REPORT_DIR = REPO_ROOT / "data" / "sil"

PASOS_LOCALES = ["review", "lessons-export", "dashboard"]
PASOS_FULL = ["review", "dispatch", "verify", "lessons-export", "dashboard"]
TIMEOUTS = {"review": 900, "dispatch": 600, "verify": 600,
            "lessons-export": 120, "dashboard": 300}


def _paso(cmd: str, timeout: int) -> dict:
    """Ejecuta `python sil_engine.py <cmd>` sin shell. Honesto con el codigo."""
    if run_cmd is None:
        return {"cmd": cmd, "returncode": 127, "tail": "safe_exec no disponible"}
    r = run_cmd([sys.executable, "sil_engine.py", cmd],
                timeout=timeout)
    out = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
    tail = "\n".join(out.splitlines()[-15:]) if out else ""
    print(f"[{cmd}] rc={r.returncode}")
    if tail:
        print(tail)
    return {"cmd": cmd, "returncode": r.returncode, "tail": tail}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Job semanal SIL")
    parser.add_argument("--full", action="store_true",
                        help="Incluye dispatch+verify (efectos externos)")
    parser.add_argument("--check", action="store_true",
                        help="Muestra que correria sin ejecutar")
    args = parser.parse_args(argv)

    pasos = PASOS_FULL if args.full else PASOS_LOCALES
    if args.check:
        print("Pasos:", " -> ".join(pasos))
        print("Modo:", "FULL (con dispatch)" if args.full else "local (seguro)")
        return 0

    print(f"SIL weekly job ({'FULL' if args.full else 'local'}) — {datetime.now():%Y-%m-%d %H:%M}")
    resultados = [_paso(cmd, TIMEOUTS.get(cmd, 300)) for cmd in pasos]

    resumen_scoreboard = None
    try:
        from agents.agent_scoreboard import Scoreboard

        resumen_scoreboard = Scoreboard().summary()
    except Exception as e:
        resumen_scoreboard = {"ok": False, "error": str(e)[:200]}

    reporte = {
        "fecha": datetime.now().isoformat(),
        "modo": "full" if args.full else "local",
        "pasos": resultados,
        "scoreboard": resumen_scoreboard,
        "ok": all(p["returncode"] == 0 for p in resultados),
    }
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        ruta = REPORT_DIR / f"weekly_report_{datetime.now():%Y-%m-%d}.json"
        ruta.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Reporte: {ruta}")
    except Exception as e:
        print(f"No se pudo escribir el reporte: {e}")

    print("OK" if reporte["ok"] else "FALLOS (ver reporte)")
    return 0 if reporte["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

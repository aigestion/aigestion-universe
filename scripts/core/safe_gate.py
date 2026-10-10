"""Compat shim (Fase 3, 1-2 sprints). No editar: la fuente de verdad vive en
sil/safe_gate.py. Existe solo para no romper
scripts/hooks externos que hacen `import safe_gate`
o invocan su CLI (`python safe_gate.py check`)."""

from sil.safe_gate import *  # noqa: F401, F403

if __name__ == "__main__":
    import sys

    sys.exit(main())  # noqa: F405 — re-exportado del modulo real

"""Compat shim (Fase 3, 1-2 sprints). No editar: la fuente de verdad vive en
sil/safe_gate.py. Existe solo para no romper
scripts/hooks externos que hacen `import safe_gate`
o invocan su CLI (`python safe_gate.py check`)."""

import sys as _sys
from pathlib import Path as _Path

# La raiz del repo debe estar en el path para que `sil.safe_gate` resuelva.
# Se APPENDE (no insert) para no desplazar modulos ya cargados.
_raiz = str(_Path(__file__).resolve().parents[1])
if _raiz not in _sys.path:
    _sys.path.append(_raiz)

from sil.safe_gate import *  # noqa: E402, F401, F403

if __name__ == "__main__":
    import sys

    sys.exit(main())  # noqa: F405 — re-exportado del modulo real

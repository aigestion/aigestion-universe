"""Compat shim. No editar: la fuente de verdad vive en
core/safe_exec.py. Existe solo para no romper
scripts externos que hacen `import safe_exec`."""

import sys
from pathlib import Path

_raiz = Path(__file__).resolve().parents[1]
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

from core.safe_exec import *  # noqa: E402,F401,F403

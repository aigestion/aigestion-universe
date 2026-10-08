"""Shared loading of :mod:`phone.core.metrics` from agent modules.

The agents are imported by file path (see ``phone.core.registry``) rather than
as a package, so a plain relative import cannot resolve. Each agent therefore
loads this helper by path and reads the measurement functions off it.

Kept in one place so the sixteen subagents that need it do not each carry their
own copy of the fallback logic.
"""

from __future__ import annotations

import importlib.util
import pathlib
from types import ModuleType

__all__ = ["load_metrics"]

_CACHE: dict = {}


def load_metrics() -> ModuleType:
    """Import ``phone/core/metrics.py`` by path, caching the module.

    Returns:
        The metrics module. Raises nothing on the happy path; a missing file
        surfaces as an ImportError, which is correct because the agents that
        depend on it genuinely cannot measure anything without it.
    """
    if "metrics" in _CACHE:
        return _CACHE["metrics"]
    target = pathlib.Path(__file__).resolve().with_name("metrics.py")
    spec = importlib.util.spec_from_file_location("_aig_metrics", target)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load metrics module from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _CACHE["metrics"] = module
    return module

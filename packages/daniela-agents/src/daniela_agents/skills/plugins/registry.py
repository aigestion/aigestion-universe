"""Plugin registry — contract + allowlist + signed loading.

现状: `plugins/` es una isla (32+ modulos) que ningun codigo importa en el
proceso principal; `agents/plugin_health.py` los audita en subproceso.
Este modulo es el punto de carga OBLIGATORIO cuando eso cambie:

  from plugins.registry import load
  mod = load("notifier")          # ok si esta en ALLOWLIST y el hash coincide
  mod = load("evil")              # PluginRefused: no registrado

Reglas:
  * Solo lo listado en ALLOWLIST carga. Nada de discovery implicito.
  * Cada entrada fija `permissions` (net, fs-read, fs-write, exec, browser).
    El loader NO las hace cumplir (eso exige sandbox); existen para que el
    revisor las vea y para que el futuro sandbox las aplique.
  * `sha256` opcional: si se fija, el fichero debe coincidir o se rechaza.
    Sin sha256, cualquier cambio en disco pasa (documentado, no silencioso).

Para dar de alta un plugin: auditarlo (plugin_health en verde + revision
humana), fijar version+sha256 y anadirlo a ALLOWLIST en este fichero.
"""
from __future__ import annotations

import hashlib
import importlib
from dataclasses import dataclass, field
from pathlib import Path

PLUGINS_DIR = Path(__file__).resolve().parent

PERMISSIONS = frozenset({"net", "fs-read", "fs-write", "exec", "browser"})


class PluginRefused(Exception):
    """Raised when a plugin cannot be loaded (not listed / hash mismatch)."""


@dataclass(frozen=True)
class Plugin:
    name: str
    version: str
    entry: str  # module path inside plugins/, e.g. "notifier"
    permissions: frozenset = field(default_factory=frozenset)
    sha256: str = ""  # hex digest of the entry file; "" = unchecked

    def __post_init__(self):
        unknown = set(self.permissions) - PERMISSIONS
        if unknown:
            raise ValueError(f"permisos desconocidos en {self.name}: {sorted(unknown)}")


# Curated allowlist. EMPTY by default: every entry below passed
# plugin_health + human review. Add entries here, never elsewhere.
#
# Historial: notifier+memory (1a tanda) -> +sensors/location/integrity_guard/
# tts_bridge/scheduler/briefing (2a, con scheduler conectado al registry) ->
# +hardware_ctrl/net_audit/power_saver/sentinel/status/uptime (3a).
ALLOWLIST: dict[str, Plugin] = {
    "notifier": Plugin(
        name="notifier", version="1.0.0", entry="notifier",
        permissions=frozenset({"exec"}),
        sha256="5ba5febfbd66c35452c8e313c0d828ff1f6da126b0e699214eca9f9cad783d3a",
    ),
    "memory": Plugin(
        name="memory", version="1.0.0", entry="memory",
        permissions=frozenset({"fs-read", "fs-write"}),
        sha256="c1705ffea592d01be9d5eb3b3197437e7f1211fa8d713f078856dca44f19a4dd",
    ),
    # Auditados 2026-09-23 (2a tanda): subprocess con argv fijo termux-*
    # (sensors/location/tts_bridge), hashing local de ficheros
    # (integrity_guard), scheduler conectado al registry (solo allowlist),
    # briefing una vez auditada su cadena transitiva.
    "sensors": Plugin(
        name="sensors", version="1.0.0", entry="sensors",
        permissions=frozenset({"exec"}),
        sha256="566f28e75fadc312d5aee7a7dbc20a3b2f68d9a0fee6edd163c055f63f3cefbf",
    ),
    "location": Plugin(
        name="location", version="1.0.0", entry="location",
        permissions=frozenset({"exec"}),
        sha256="67dfd71f7f451e249e34e1145c756e44ad5910f36e19da9addf85817f6eb93ab",
    ),
    "integrity_guard": Plugin(
        name="integrity_guard", version="1.0.0", entry="integrity_guard",
        permissions=frozenset({"fs-read", "fs-write"}),
        sha256="03d17bdfcdd3224832eb83d673089f4b372a6f5e95fe140a2db80f0ac58f4fa1",
    ),
    "tts_bridge": Plugin(
        name="tts_bridge", version="1.0.0", entry="tts_bridge",
        permissions=frozenset({"exec"}),
        sha256="7783556252d61170303882f9669895c558fb26089d6316e7d6de8c40533cd6e7",
    ),
    "scheduler": Plugin(
        name="scheduler", version="1.0.0", entry="scheduler",
        permissions=frozenset({"exec"}),
        sha256="2a356ade71b8330246c4e92a84d2323e96c5c7b68f99f8b2d4cd212710a93189",
    ),
    "briefing": Plugin(
        name="briefing", version="1.0.0", entry="briefing",
        permissions=frozenset({"exec"}),
        sha256="f2324807eed79b417b6518241d01849395015743dae6050422ad55d650cefc32",
    ),
    # Auditados 2026-09-23 (3a tanda): introspeccion con argv fijo
    # (termux-*, ip, uptime). Sin red, sin shell, sin eval.
    "hardware_ctrl": Plugin(
        name="hardware_ctrl", version="1.0.0", entry="hardware_ctrl",
        permissions=frozenset({"exec"}),
        sha256="6c02ae04ef18483b3dc400f2b80eff2180dc4433aa3521e2cfa25d5be0665d31",
    ),
    "net_audit": Plugin(
        name="net_audit", version="1.0.0", entry="net_audit",
        permissions=frozenset({"exec"}),
        sha256="76ed3fa55156b9a1f8842da373d66f0e98c36bf93e53d983d158433247fd1c0f",
    ),
    "power_saver": Plugin(
        name="power_saver", version="1.0.0", entry="power_saver",
        permissions=frozenset({"exec"}),
        sha256="a3f03a9643b6948392e4213694359ae181dd5cfdc8ca8c68b97187d010d29ed3",
    ),
    "sentinel": Plugin(
        name="sentinel", version="1.0.0", entry="sentinel",
        permissions=frozenset({"exec"}),
        sha256="34d9389436a24da68dc51e08359542eecbf5e40fd5b7938658c27aaabc9fb25d",
    ),
    "status": Plugin(
        name="status", version="1.0.0", entry="status",
        permissions=frozenset({"exec"}),
        sha256="ba9fb80d885ee87b09032a21a4cf3f3e28ca8267b23528604bb96f9523a3edca",
    ),
    "uptime": Plugin(
        name="uptime", version="1.0.0", entry="uptime",
        permissions=frozenset({"exec"}),
        sha256="4f23c9aadc645597ba84d6cd0a40b08fdfad1832ea4b88a11d8c678e9f23adf5",
    ),
}


def _digest(entry: str) -> str:
    target = (PLUGINS_DIR / (entry.replace(".", "/") + ".py")).resolve()
    if PLUGINS_DIR not in target.parents:
        raise PluginRefused(f"entry fuera de plugins/: {entry!r}")
    if not target.is_file():
        raise PluginRefused(f"entry inexistente: {entry!r}")
    content = target.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def audit() -> list[dict]:
    """Inventory of plugins/ (no imports, no execution)."""
    rows = []
    for f in sorted(PLUGINS_DIR.glob("*.py")):
        if f.name in ("__init__.py", "registry.py"):
            continue
        rows.append({
            "name": f.stem,
            "registered": f.stem in ALLOWLIST,
            "sha256": hashlib.sha256(
                f.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            ).hexdigest()[:16],
        })
    return rows


def load(name: str):
    """Import an allowlisted plugin or refuse with PluginRefused."""
    plugin = ALLOWLIST.get(name)
    if plugin is None:
        raise PluginRefused(
            f"{name!r} no esta en ALLOWLIST (plugins/registry.py). "
            "Auditalo con plugin_health + revision humana y dalo de alta."
        )
    if plugin.sha256 and _digest(plugin.entry) != plugin.sha256:
        raise PluginRefused(f"{name!r} cambio en disco (hash no coincide)")
    return importlib.import_module(f"plugins.{plugin.entry}")


def repin() -> dict[str, str]:
    """Recalculates current sha256 for every ALLOWLIST entry.

    Needed after mechanical changes (ruff --fix, formatting): the pin
    records exact bytes, so any edit —even whitespace— breaks it BY DESIGN
    (test_entradas_registradas_cargan fails loudly). Re-audit the diff,
    then copy the printed values into ALLOWLIST.
    """
    return {name: _digest(p.entry) for name, p in ALLOWLIST.items()}

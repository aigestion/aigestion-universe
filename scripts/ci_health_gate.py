"""Health gate for the 21 AIG engines. Stdlib only.

Perfil gateway (legado): 20 motores del mapa del gateway.
Shim de compatibilidad sobre `scripts/core/ci_health_gate.py` (canónico: lo
que `config/docker-compose.prod.yml` despliega de verdad). Toda la lógica
vive en el canónico; aquí solo queda la lista ENGINES del mapa gateway y dos
envoltorios finos (`check`/`main`) que la usan.

Uso:
    python scripts/ci_health_gate.py --base-url http://localhost --fail-under 95
    python scripts/ci_health_gate.py http://localhost --fail-under 100 --only intel_engine,auto_engine
    python scripts/ci_health_gate.py --base-url http://localhost --json
"""

import importlib.util
import json
import pathlib
import sys
import urllib.request  # noqa: F401  # tests/test_ci_health_gate.py lo mockea: mod.urllib.request.urlopen

# 20 engines matching the gateway map: (name, port, status path).
# Lista legacy: se conserva tal cual porque `tests/test_ci_health_gate.py`
# la afirma entera y el perfil gateway la sigue necesitando.
ENGINES = [
    {"name": "epic_pc", "port": 5020, "path": "/api/status"},
    {"name": "daniela", "port": 9200, "path": "/api/status"},
    {"name": "hermes", "port": 9300, "path": "/api/status"},
    {"name": "optimization", "port": 9400, "path": "/api/opt/status"},
    {"name": "frontend", "port": 9500, "path": "/api/frontend/status"},
    {"name": "infra_opt", "port": 9700, "path": "/api/infra/status"},
    {"name": "agent_mobile", "port": 9800, "path": "/api/agent/status"},
    {"name": "security", "port": 9999, "path": "/api/secure/status"},
    {"name": "perf", "port": 9998, "path": "/api/perf/status"},
    {"name": "dashboard", "port": 9997, "path": "/api/status"},
    {"name": "intel_engine", "port": 9850, "path": "/api/intel/status"},
    {"name": "auto_engine", "port": 9860, "path": "/api/auto/status"},
    {"name": "data_engine", "port": 9870, "path": "/api/data/status"},
    {"name": "secure_engine", "port": 9880, "path": "/api/secure_engine/status"},
    {"name": "devtools_engine", "port": 9890, "path": "/api/devtools/status"},
    {"name": "ecosystem_engine", "port": 9840, "path": "/api/ecosystem/status"},
    {"name": "ux_engine", "port": 9830, "path": "/api/ux/status"},
    {"name": "scale_engine", "port": 9820, "path": "/api/scale/status"},
    {"name": "chaos_engine", "port": 9910, "path": "/api/chaos/status"},
    {"name": "regions", "port": 9911, "path": "/api/regions/status", "status_key": None},
]

_CANON_PATH = pathlib.Path(__file__).resolve().parent / "core" / "ci_health_gate.py"


def _load_canon():
    spec = importlib.util.spec_from_file_location("_ci_health_gate_core", str(_CANON_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_canon = _load_canon()

# Lógica canónica reexportada (una sola implementación).
HEALTHY_STATUSES = _canon.HEALTHY_STATUSES
es_base_local = _canon.es_base_local
instalar_opener_sin_proxy = _canon.instalar_opener_sin_proxy
build_url = _canon.build_url
check_engine = _canon.check_engine
summarize = _canon.summarize
parse_args = _canon.parse_args


def check(base_url, timeout=4, only=None, noproxy=None):
    """Check all (or a subset of) gateway engines. Returns result dicts.

    Idéntico a `scripts/core/ci_health_gate.py:check` pero sobre la lista
    legacy ENGINES de este módulo (20 motores del mapa gateway).
    """
    if noproxy is None:
        noproxy = es_base_local(base_url)
    if noproxy:
        instalar_opener_sin_proxy()
    selected = ENGINES
    if only:
        wanted = {name.strip() for name in only if name.strip()}
        selected = [e for e in ENGINES if e["name"] in wanted]
    return [check_engine(base_url, engine, timeout=timeout) for engine in selected]


def main(argv=None, base_url=None, fail_under=95.0, timeout=4.0, only=None, noproxy=None):
    """Entry point. Prints JSON summary, returns exit code (0 pass / 1 fail).

    Misma semántica que el canónico (incluido el arreglo del bug CLI del
    2026-09-17: con `argv=None` se parsea `sys.argv`; con `base_url` dado no
    se toca `sys.argv`).
    """
    if base_url is None:
        # Camino CLI: parsear sys.argv (o el argv explicito si lo hay).
        base_url, fail_under, timeout, only, noproxy = parse_args(argv)
    results = check(base_url, timeout=timeout, only=only, noproxy=noproxy)
    summary = summarize(results, fail_under=fail_under, base_url=base_url)
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

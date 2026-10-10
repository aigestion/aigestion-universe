"""Per-engine resource budgets for all AIG engines (stdlib only).

Ports mirror ``cross_engine.protocols.ENGINE_PORTS`` plus:
- gateway  -> 8080 (cross_engine.gateway)
- chaos    -> 9910 (chaos_engine.server)
- regions  -> 9911 (multi-region.server; also serves drills via
  POST /api/regions/drill, hence "regions drills")

Total rows: 22 (19 ENGINE_PORTS + gateway + chaos + regions).
"""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class EngineBudget:
    name: str
    port: int
    tier: str  # critical | standard | batch
    cpu_limit: float
    mem_limit_mb: int
    replicas: int
    p99_ms_budget: int
    error_budget_pct: float
    rps_expected: int


_BUDGETS: dict[str, EngineBudget] = {
    # --- Critical (6) ---
    "daniela": EngineBudget("daniela", 9200, "critical", 4.0, 4096, 3, 250, 0.1, 200),
    "hermes": EngineBudget("hermes", 9300, "critical", 2.0, 2048, 3, 300, 0.1, 150),
    "dashboard": EngineBudget("dashboard", 9997, "critical", 2.0, 2048, 2, 300, 0.1, 150),
    "gateway": EngineBudget("gateway", 8080, "critical", 4.0, 4096, 3, 150, 0.1, 500),
    "security": EngineBudget("security", 9999, "critical", 2.0, 2048, 2, 200, 0.1, 200),
    "perf": EngineBudget("perf", 9998, "critical", 2.0, 2048, 2, 200, 0.1, 100),
    # --- Batch (2): chaos + regions (regions serves drills) ---
    "chaos": EngineBudget("chaos", 9910, "batch", 0.5, 512, 1, 2000, 1.0, 5),
    "regions": EngineBudget("regions", 9911, "batch", 1.0, 1024, 1, 1000, 1.0, 20),
    # --- Standard (14): rest of ENGINE_PORTS ---
    "epic_pc": EngineBudget("epic_pc", 5020, "standard", 1.0, 1024, 1, 500, 0.5, 50),
    "optimization": EngineBudget("optimization", 9400, "standard", 1.0, 1024, 1, 600, 0.5, 50),
    "frontend_v1": EngineBudget("frontend_v1", 9500, "standard", 1.0, 1024, 2, 400, 0.5, 100),
    "frontend_v2": EngineBudget("frontend_v2", 9600, "standard", 1.0, 1024, 2, 400, 0.5, 100),
    "infra_opt": EngineBudget("infra_opt", 9700, "standard", 1.0, 1024, 1, 600, 0.5, 30),
    "agent_mobile": EngineBudget("agent_mobile", 9800, "standard", 1.0, 1024, 1, 500, 0.5, 50),
    "intel_engine": EngineBudget("intel_engine", 9850, "standard", 1.0, 2048, 1, 600, 0.5, 40),
    "auto_engine": EngineBudget("auto_engine", 9860, "standard", 1.0, 1024, 1, 700, 0.5, 30),
    "data_engine": EngineBudget("data_engine", 9870, "standard", 2.0, 2048, 1, 700, 0.5, 40),
    "secure_engine": EngineBudget("secure_engine", 9880, "standard", 1.0, 1024, 1, 500, 0.5, 40),
    "devtools_engine": EngineBudget("devtools_engine", 9890, "standard", 0.5, 512, 1, 800, 0.5, 20),
    "ecosystem_engine": EngineBudget("ecosystem_engine", 9840, "standard", 1.0, 1024, 1, 600, 0.5, 30),
    "ux_engine": EngineBudget("ux_engine", 9830, "standard", 0.5, 512, 1, 500, 0.5, 30),
    "scale_engine": EngineBudget("scale_engine", 9820, "standard", 1.0, 1024, 2, 400, 0.5, 80),
}


def get_budget(name: str) -> EngineBudget:
    """Return the budget for engine ``name`` (KeyError if unknown)."""
    return _BUDGETS[name]


def all_budgets() -> list[EngineBudget]:
    """Return all engine budgets sorted by name."""
    return [_BUDGETS[k] for k in sorted(_BUDGETS)]


def total_resources() -> dict:
    """Return cluster-wide resource totals.

    Returns dict with ``cpu`` (cores), ``mem_mb`` and ``replicas``.
    """
    cpu = round(sum(b.cpu_limit for b in _BUDGETS.values()), 2)
    mem = sum(b.mem_limit_mb for b in _BUDGETS.values())
    replicas = sum(b.replicas for b in _BUDGETS.values())
    return {"cpu": cpu, "mem_mb": mem, "replicas": replicas}


def to_dict(budget: EngineBudget) -> dict:
    """Convert an EngineBudget to a plain dict."""
    return asdict(budget)

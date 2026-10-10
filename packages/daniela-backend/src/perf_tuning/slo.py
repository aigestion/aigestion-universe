"""SLO definitions per tier (stdlib only)."""

from .budgets import EngineBudget

AVAILABILITY_TARGETS: dict[str, float] = {
    "critical": 99.9,
    "standard": 99.5,
    "batch": 99.0,
}

# Fraction of budget consumption that triggers a "warn" (80%).
WARN_RATIO = 0.8


def availability_target(tier: str) -> float:
    """Return availability SLO (%) for a tier (KeyError if unknown)."""
    return AVAILABILITY_TARGETS[tier]


def latency_target(budget: EngineBudget) -> int:
    """Return p99 latency target (ms) for a budget."""
    return budget.p99_ms_budget


def error_budget_remaining(allowed_pct: float, observed_pct: float) -> float:
    """Return remaining error budget in percentage points.

    Positive = budget left, zero = exactly exhausted, negative = overrun.
    """
    return allowed_pct - observed_pct


def burn_rate(observed_pct: float, allowed_pct: float) -> float:
    """Return error-budget burn rate (observed / allowed).

    > 1 means breaching (consuming budget faster than allowed).
    Returns ``inf`` when allowed is 0 and observed > 0, else 0.0.
    """
    if allowed_pct == 0:
        if observed_pct > 0:
            return float("inf")
        return 0.0
    return observed_pct / allowed_pct


def evaluate(observed_latency_p99: float, observed_error_pct: float, budget: EngineBudget) -> dict:
    """Evaluate observed metrics against a budget.

    - ``breach``: latency > p99 budget OR burn rate > 1 (error over budget).
    - ``warn``: at >=80% of either budget but not breaching.
    - ``pass``: comfortably within both budgets.

    Returns dict with ``status``, ``remaining`` (error budget left, pp),
    ``burn_rate``, ``latency_ok``, ``error_ok`` and ``availability_target``.
    """
    allowed = budget.error_budget_pct
    remaining = error_budget_remaining(allowed, observed_error_pct)
    burn = burn_rate(observed_error_pct, allowed)
    latency_ok = observed_latency_p99 <= budget.p99_ms_budget
    error_ok = burn <= 1.0

    latency_ratio = (observed_latency_p99 / budget.p99_ms_budget) if budget.p99_ms_budget else 0.0

    if not latency_ok or not error_ok:
        status = "breach"
    elif burn >= WARN_RATIO or latency_ratio >= WARN_RATIO:
        status = "warn"
    else:
        status = "pass"

    return {
        "status": status,
        "remaining": remaining,
        "burn_rate": burn,
        "latency_ok": latency_ok,
        "error_ok": error_ok,
        "latency_ratio": latency_ratio,
        "availability_target": AVAILABILITY_TARGETS[budget.tier],
        "budget": budget.name,
    }

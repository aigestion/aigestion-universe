"""Rightsizing suggestions per engine (stdlib only)."""

from .budgets import EngineBudget, all_budgets, total_resources

# Usage fractions driving suggestions.
DOWNSIZE_BELOW = 0.30
UPSIZE_ABOVE = 0.85

MIN_CPU = 0.25
MIN_MEM_MB = 128


def rightsize(
    current_cpu: float,
    current_mem: int,
    usage_cpu: float,
    usage_mem: int,
    budget: EngineBudget,
) -> dict:
    """Suggest downsize/keep/upsize given allocation vs actual usage.

    - downsize: both cpu and mem usage < 30% of current allocation.
    - upsize: either cpu or mem usage > 85% of current allocation.
    - keep: otherwise.

    Returns dict with ``action``, ``reason``, ``suggested_cpu``,
    ``suggested_mem``, ``cpu_pct`` and ``mem_pct``.
    """
    cpu_pct = (usage_cpu / current_cpu) if current_cpu > 0 else 0.0
    mem_pct = (usage_mem / current_mem) if current_mem > 0 else 0.0

    if cpu_pct < DOWNSIZE_BELOW and mem_pct < DOWNSIZE_BELOW:
        suggested_cpu = max(round(current_cpu * 0.5, 2), MIN_CPU)
        suggested_mem = max(int(current_mem * 0.5), MIN_MEM_MB)
        return {
            "action": "downsize",
            "reason": (
                f"low usage: cpu {cpu_pct:.0%} / mem {mem_pct:.0%} "
                f"of current (both < {DOWNSIZE_BELOW:.0%})"
            ),
            "suggested_cpu": suggested_cpu,
            "suggested_mem": suggested_mem,
            "cpu_pct": cpu_pct,
            "mem_pct": mem_pct,
        }

    if cpu_pct > UPSIZE_ABOVE or mem_pct > UPSIZE_ABOVE:
        suggested_cpu = round(current_cpu * 1.5, 2)
        suggested_mem = int(current_mem * 1.5)
        over = []
        if suggested_cpu > budget.cpu_limit:
            over.append(f"suggested cpu {suggested_cpu} exceeds budget {budget.cpu_limit}")
        if suggested_mem > budget.mem_limit_mb:
            over.append(f"suggested mem {suggested_mem}MB exceeds budget {budget.mem_limit_mb}MB")
        reason = (
            f"high usage: cpu {cpu_pct:.0%} / mem {mem_pct:.0%} "
            f"of current (either > {UPSIZE_ABOVE:.0%})"
        )
        if over:
            reason += "; " + "; ".join(over)
        return {
            "action": "upsize",
            "reason": reason,
            "suggested_cpu": suggested_cpu,
            "suggested_mem": suggested_mem,
            "cpu_pct": cpu_pct,
            "mem_pct": mem_pct,
        }

    return {
        "action": "keep",
        "reason": (
            f"healthy usage: cpu {cpu_pct:.0%} / mem {mem_pct:.0%} "
            f"of current (within {DOWNSIZE_BELOW:.0%}-{UPSIZE_ABOVE:.0%})"
        ),
        "suggested_cpu": current_cpu,
        "suggested_mem": current_mem,
        "cpu_pct": cpu_pct,
        "mem_pct": mem_pct,
    }


def _split_usage(entry) -> tuple[float, float, float, float]:
    """Extract (current_cpu, current_mem, usage_cpu, usage_mem) from a usage entry.

    Accepts dicts with keys ``current_cpu``/``current_mem`` (fallback: budget
    limits) and ``usage_cpu``/``usage_mem`` (fallback aliases ``cpu``/``mem``),
    or a 2/4-tuple (usage_cpu, usage_mem[, current_cpu, current_mem]).
    """
    if isinstance(entry, (list, tuple)):
        if len(entry) == 2:
            return (0.0, 0, float(entry[0]), float(entry[1]))
        if len(entry) == 4:
            return (float(entry[2]), float(entry[3]), float(entry[0]), float(entry[1]))
        raise ValueError(f"usage tuple must have 2 or 4 items, got {len(entry)}")
    if isinstance(entry, dict):
        return (
            float(entry.get("current_cpu", 0) or 0),
            float(entry.get("current_mem", 0) or 0),
            float(entry.get("usage_cpu", entry.get("cpu", 0)) or 0),
            float(entry.get("usage_mem", entry.get("mem", 0)) or 0),
        )
    raise ValueError(f"unsupported usage entry: {entry!r}")


def generate_report(usages: dict) -> dict:
    """Build a rightsizing report for the cluster.

    ``usages`` maps engine name -> usage entry (see ``_split_usage``).
    Engines missing from ``usages`` default to 50% of their budget (keep).

    Returns dict with ``suggestions`` (per engine), ``totals``
    (cluster resources) and ``savings`` (cpu/mem reclaimable via downsize
    plus action counts).
    """
    suggestions: dict[str, dict] = {}
    cpu_saved = 0.0
    mem_saved = 0
    counts = {"downsize": 0, "keep": 0, "upsize": 0}

    for budget in all_budgets():
        entry = usages.get(budget.name)
        if entry is None:
            current_cpu, current_mem = budget.cpu_limit, budget.mem_limit_mb
            usage_cpu, usage_mem = current_cpu * 0.5, current_mem * 0.5
        else:
            current_cpu, current_mem, usage_cpu, usage_mem = _split_usage(entry)
            if not current_cpu:
                current_cpu = budget.cpu_limit
            if not current_mem:
                current_mem = budget.mem_limit_mb
        suggestion = rightsize(current_cpu, int(current_mem), usage_cpu, usage_mem, budget)
        suggestions[budget.name] = suggestion
        counts[suggestion["action"]] = counts.get(suggestion["action"], 0) + 1
        if suggestion["action"] == "downsize":
            cpu_saved += current_cpu - suggestion["suggested_cpu"]
            mem_saved += int(current_mem) - suggestion["suggested_mem"]

    totals = total_resources()
    return {
        "suggestions": suggestions,
        "totals": totals,
        "savings": {
            "cpu_saved": round(cpu_saved, 2),
            "mem_mb_saved": mem_saved,
            "downsize_count": counts.get("downsize", 0),
            "upsize_count": counts.get("upsize", 0),
            "keep_count": counts.get("keep", 0),
        },
    }

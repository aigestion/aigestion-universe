"""
aig Multi-Region DNS Weight Simulator
=============================================
In-memory weighted routing table per region. Simulation only:
no real DNS changes are ever performed.

Autor: aig Team
"""

from __future__ import annotations

import random
import time
from typing import Any

try:
    from .config import REGIONS
except ImportError:
    from config import REGIONS


class DnsWeightTable:
    """Weighted routing table simulator (no real DNS side effects)."""

    def __init__(self, initial: dict[str, float] | None = None) -> None:
        if initial is not None:
            for name in initial:
                if name not in REGIONS:
                    raise ValueError(f"Unknown region: {name}")
            weights = {name: float(initial.get(name, 0.0)) for name in REGIONS}
        else:
            weights = self._equal_weights()
        self._default: dict[str, float] = dict(weights)
        self._weights: dict[str, float] = dict(weights)
        self._history: list[dict[str, Any]] = []

    @staticmethod
    def _equal_weights() -> dict[str, float]:
        names = list(REGIONS.keys())
        n = len(names)
        if n == 0:
            return {}
        share = round(1.0 / n, 4)
        weights = dict.fromkeys(names, share)
        # Fix rounding dust on the last region so weights sum to 1.0.
        weights[names[-1]] = round(1.0 - share * (n - 1), 4)
        return weights

    # ── Reads ──────────────────────────────────────────────────

    def get_table(self) -> dict[str, float]:
        """Return a copy of the current weight table."""
        return dict(self._weights)

    def get_weight(self, region_name: str) -> float:
        """Return the current weight of a region."""
        if region_name not in REGIONS:
            raise ValueError(f"Unknown region: {region_name}")
        return self._weights[region_name]

    def get_history(self) -> list[dict[str, Any]]:
        """Return the weight-change history."""
        return list(self._history)

    # ── Mutations (simulated) ──────────────────────────────────

    def set_weight(self, region_name: str, weight: float) -> dict[str, float]:
        """Set an explicit weight (0.0 - 1.0)."""
        if region_name not in REGIONS:
            raise ValueError(f"Unknown region: {region_name}")
        weight = float(weight)
        if not 0.0 <= weight <= 1.0:
            raise ValueError(f"Weight out of range [0, 1]: {weight}")
        self._weights[region_name] = weight
        self._history.append(
            {
                "action": "set",
                "region": region_name,
                "weight": weight,
                "timestamp": time.time(),
            }
        )
        return self.get_table()

    def shift_weight(
        self,
        from_region: str,
        to_region: str,
        amount: float | None = None,
    ) -> dict[str, float]:
        """Move weight from one region to another (simulated).

        With amount=None the full weight of from_region is moved.
        """
        if from_region not in REGIONS:
            raise ValueError(f"Unknown region: {from_region}")
        if to_region not in REGIONS:
            raise ValueError(f"Unknown region: {to_region}")
        if from_region == to_region:
            return self.get_table()

        available = self._weights[from_region]
        if amount is None:
            move = available
        else:
            move = min(max(0.0, float(amount)), available)

        self._weights[from_region] = round(available - move, 6)
        self._weights[to_region] = round(self._weights[to_region] + move, 6)
        self._history.append(
            {
                "action": "shift",
                "from": from_region,
                "to": to_region,
                "amount": round(move, 6),
                "timestamp": time.time(),
            }
        )
        return self.get_table()

    def restore(self) -> dict[str, float]:
        """Restore default weights."""
        self._weights = dict(self._default)
        self._history.append({"action": "restore", "timestamp": time.time()})
        return self.get_table()

    # ── Simulation helper ──────────────────────────────────────

    def pick_region(self) -> str:
        """Pick a region honoring current weights (weighted random)."""
        names = list(REGIONS.keys())
        total = sum(self._weights.get(n, 0.0) for n in names)
        if total <= 0:
            return names[0]
        r = random.uniform(0, total)
        cumulative = 0.0
        for name in names:
            cumulative += self._weights.get(name, 0.0)
            if r <= cumulative:
                return name
        return names[-1]

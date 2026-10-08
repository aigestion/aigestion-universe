"""
aig Global Load Balancer
================================
GeoDNS, round-robin, and weighted routing across regions.

Autor: aig Team
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from .config import REGIONS, Region, get_all_regions, get_closest_region
except ImportError:
    from config import REGIONS, Region, get_all_regions, get_closest_region


# ── Routing Strategy ───────────────────────────────────────────


class RoutingStrategy(Enum):
    GEO_DNS = "geo_dns"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"


# ── Route Result ───────────────────────────────────────────────


@dataclass
class RouteResult:
    region: str
    host: str
    strategy: str
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Canary Weight ──────────────────────────────────────────────


@dataclass
class CanaryWeight:
    region_name: str
    weight: float  # 0.0 - 1.0


# ── Global Load Balancer ──────────────────────────────────────


class GlobalLoadBalancer:
    """Routes requests to optimal region based on geography, load, or weights."""

    def __init__(self, default_strategy: RoutingStrategy = RoutingStrategy.GEO_DNS):
        self.default_strategy = default_strategy
        self._round_robin_index = 0
        self._lock = threading.Lock()
        self._canary_weights: list[CanaryWeight] = []
        self._request_log: list[RouteResult] = []
        self._region_weights: dict[str, float] = dict.fromkeys(REGIONS, 1.0)
        self._region_stats: dict[str, dict[str, int]] = {
            name: {"requests": 0, "errors": 0} for name in REGIONS
        }

    # ── Main Routing Entry Point ───────────────────────────────

    def route_request(
        self,
        lat: float,
        lon: float,
        service: str = "default",
        strategy: RoutingStrategy | None = None,
    ) -> RouteResult:
        """Route a request to the best region+host."""
        strat = strategy or self.default_strategy

        if strat == RoutingStrategy.GEO_DNS:
            result = self._route_geo_dns(lat, lon, service)
        elif strat == RoutingStrategy.ROUND_ROBIN:
            result = self._route_round_robin(lat, lon, service)
        elif strat == RoutingStrategy.WEIGHTED:
            result = self._route_weighted(lat, lon, service)
        else:
            result = self._route_geo_dns(lat, lon, service)

        self._request_log.append(result)
        self._region_stats[result.region]["requests"] += 1
        return result

    # ── GeoDNS Routing ─────────────────────────────────────────

    def _route_geo_dns(
        self, lat: float, lon: float, service: str
    ) -> RouteResult:
        region = get_closest_region(lat, lon)
        start = time.time()
        host = self._pick_host(region)
        latency = (time.time() - start) * 1000

        return RouteResult(
            region=region.name,
            host=host,
            strategy=RoutingStrategy.GEO_DNS.value,
            latency_ms=latency,
            metadata={"service": service},
        )

    # ── Round-Robin Routing ────────────────────────────────────

    def _route_round_robin(
        self, lat: float, lon: float, service: str
    ) -> RouteResult:
        regions = get_all_regions()
        with self._lock:
            idx = self._round_robin_index % len(regions)
            self._round_robin_index += 1
        region = regions[idx]
        host = self._pick_host(region)

        return RouteResult(
            region=region.name,
            host=host,
            strategy=RoutingStrategy.ROUND_ROBIN.value,
            metadata={"service": service, "rr_index": idx},
        )

    # ── Weighted Routing (Canary) ─────────────────────────────

    def _route_weighted(
        self, lat: float, lon: float, service: str
    ) -> RouteResult:
        if self._canary_weights:
            region_name = self._pick_weighted_region(self._canary_weights)
        else:
            weights = [
                CanaryWeight(name, w) for name, w in self._region_weights.items()
            ]
            region_name = self._pick_weighted_region(weights)

        region = REGIONS[region_name]
        host = self._pick_host(region)

        return RouteResult(
            region=region.name,
            host=host,
            strategy=RoutingStrategy.WEIGHTED.value,
            metadata={"service": service},
        )

    def _pick_weighted_region(self, weights: list[CanaryWeight]) -> str:
        import random

        total = sum(w.weight for w in weights)
        if total <= 0:
            return weights[0].region_name if weights else "eu-west"

        r = random.uniform(0, total)
        cumulative = 0.0
        for w in weights:
            cumulative += w.weight
            if r <= cumulative:
                return w.region_name
        return weights[-1].region_name

    # ── Configuration ──────────────────────────────────────────

    def set_canary_weights(self, weights: list[CanaryWeight]) -> None:
        self._canary_weights = weights

    def set_region_weight(self, region_name: str, weight: float) -> None:
        if region_name in REGIONS:
            self._region_weights[region_name] = max(0.0, min(1.0, weight))

    # ── Host Selection ─────────────────────────────────────────

    def _pick_host(self, region: Region) -> str:
        """Pick primary or replica based on load stats."""
        stats = self._region_stats.get(region.name, {})
        requests = stats.get("requests", 0)

        if requests > 0 and requests % 10 == 0 and region.replica_hosts:
            idx = (requests // 10) % len(region.replica_hosts)
            return region.replica_hosts[idx]
        return region.primary_host

    # ── Stats & Observability ──────────────────────────────────

    def get_stats(self) -> dict[str, dict[str, int]]:
        return {
            region: dict(counts) for region, counts in self._region_stats.items()
        }

    def get_request_log(self) -> list[RouteResult]:
        return list(self._request_log)

    def get_region_for_host(self, host: str) -> str | None:
        for name, region in REGIONS.items():
            if host in region.full_hosts():
                return name
        return None

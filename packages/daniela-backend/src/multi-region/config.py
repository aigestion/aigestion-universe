"""
aig Multi-Region Config
==============================
Region definitions, failover chains, and closest-region selection.

Autor: aig Team
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# ── Region Dataclass ───────────────────────────────────────────


@dataclass
class Region:
    """Represents a deployment region."""

    name: str
    primary_host: str
    replica_hosts: list[str] = field(default_factory=list)
    latency_threshold_ms: int = 200
    failover_order: int = 0
    lat: float = 0.0
    lon: float = 0.0
    is_active: bool = True

    def full_hosts(self) -> list[str]:
        return [self.primary_host] + self.replica_hosts


# ── Region Registry ────────────────────────────────────────────

REGIONS: dict[str, Region] = {
    "eu-west": Region(
        name="eu-west",
        primary_host="eu-west-primary.aig.local:8080",
        replica_hosts=[
            "eu-west-replica-1.aig.local:8080",
            "eu-west-replica-2.aig.local:8080",
        ],
        latency_threshold_ms=150,
        failover_order=0,
        lat=40.4168,
        lon=-3.7038,
    ),
    "us-east": Region(
        name="us-east",
        primary_host="us-east-primary.aig.local:8080",
        replica_hosts=[
            "us-east-replica-1.aig.local:8080",
        ],
        latency_threshold_ms=200,
        failover_order=1,
        lat=37.4316,
        lon=-79.1000,
    ),
    "ap-south": Region(
        name="ap-south",
        primary_host="ap-south-primary.aig.local:8080",
        replica_hosts=[
            "ap-south-replica-1.aig.local:8080",
        ],
        latency_threshold_ms=250,
        failover_order=2,
        lat=19.0760,
        lon=72.8777,
    ),
}

# ── Failover Chain ─────────────────────────────────────────────

FAILOVER_CHAIN: dict[str, list[str]] = {
    "eu-west": ["us-east", "ap-south"],
    "us-east": ["ap-south", "eu-west"],
    "ap-south": ["eu-west", "us-east"],
}


# ── Public API ─────────────────────────────────────────────────


def get_region(name: str) -> Region | None:
    """Get a region by name."""
    return REGIONS.get(name)


def get_all_regions() -> list[Region]:
    """Return all registered regions sorted by failover_order."""
    return sorted(REGIONS.values(), key=lambda r: r.failover_order)


def get_failover_targets(region_name: str) -> list[str]:
    """Get ordered failover targets for a region."""
    return FAILOVER_CHAIN.get(region_name, [])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on Earth (km)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_closest_region(lat: float, lon: float) -> Region:
    """Return the region closest to the given coordinates."""
    best: Region | None = None
    best_dist = float("inf")
    for region in REGIONS.values():
        if not region.is_active:
            continue
        dist = _haversine_km(lat, lon, region.lat, region.lon)
        if dist < best_dist:
            best_dist = dist
            best = region
    if best is None:
        raise ValueError("No active regions available")
    return best

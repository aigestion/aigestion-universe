"""
aig Multi-Region Deployment
===================================
Phase 4: Multi-region config, replication, failover, and load balancing.

Autor: aig Team

Note: Directory uses hyphen (multi-region) for filesystem convention.
Python imports use sys.path manipulation or importlib for submodules.
"""

__all__ = [
    "Region",
    "REGIONS",
    "FAILOVER_CHAIN",
    "get_region",
    "get_all_regions",
    "get_failover_targets",
    "get_closest_region",
    "ConflictStrategy",
    "ReplicationRecord",
    "ReplicationManager",
    "RegionStatus",
    "HealthCheckResult",
    "FailoverEvent",
    "FailoverManager",
    "RoutingStrategy",
    "RouteResult",
    "CanaryWeight",
    "GlobalLoadBalancer",
]

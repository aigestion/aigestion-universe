"""Simulated faults. No external deps.

Real injection (SIGKILL, tc, cgroups, iptables) is unsafe in shared/test
environments, so every fault here simulates via in-process flags only.
inject() sets the fault active; recover() clears it. Safe by design.
"""

from __future__ import annotations

import time
from typing import Any


class Fault:
    """Base fault: in-process simulation flag."""

    fault_type: str = "base"

    def __init__(self, target: str = "default", duration: float = 60.0, **kwargs: Any) -> None:
        self.name: str = getattr(self, "fault_type", self.__class__.__name__)
        self.target = target
        self.duration = float(duration)
        self.extra: dict[str, Any] = dict(kwargs)
        self.active = False
        self.injected_at: float | None = None
        self.recovered_at: float | None = None

    def inject(self) -> bool:
        """Simulate fault injection. Returns True when now active."""
        self.active = True
        self.injected_at = time.time()
        return True

    def recover(self) -> bool:
        """Recover simulated fault. Returns True when now inactive."""
        self.active = False
        self.recovered_at = time.time()
        return True

    def is_active(self) -> bool:
        return self.active

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.fault_type,
            "target": self.target,
            "duration": self.duration,
            "active": self.active,
            "extra": self.extra,
        }

    def __enter__(self) -> Fault:
        self.inject()
        return self

    def __exit__(self, *exc: Any) -> bool:
        self.recover()
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(target={self.target!r}, duration={self.duration}, active={self.active})"


class KillProcess(Fault):
    fault_type = "kill_process"

    def __init__(self, target: str = "default", duration: float = 60.0, signal: str = "SIGKILL", **kw: Any) -> None:
        super().__init__(target, duration, signal=signal, **kw)
        self.name = self.fault_type
        self.signal = signal


class LatencyInjection(Fault):
    fault_type = "latency_injection"

    def __init__(self, target: str = "default", duration: float = 60.0, latency_ms: float = 1000.0, **kw: Any) -> None:
        super().__init__(target, duration, latency_ms=latency_ms, **kw)
        self.name = self.fault_type
        self.latency_ms = float(latency_ms)


class CPUStress(Fault):
    fault_type = "cpu_stress"

    def __init__(self, target: str = "default", duration: float = 60.0, cpu_percent: float = 90.0, workers: int = 2, **kw: Any) -> None:
        super().__init__(target, duration, cpu_percent=cpu_percent, workers=workers, **kw)
        self.name = self.fault_type
        self.cpu_percent = float(cpu_percent)
        self.workers = int(workers)


class MemoryStress(Fault):
    fault_type = "memory_stress"

    def __init__(self, target: str = "default", duration: float = 60.0, size_mb: float = 512.0, **kw: Any) -> None:
        super().__init__(target, duration, size_mb=size_mb, **kw)
        self.name = self.fault_type
        self.size_mb = float(size_mb)
        self._buffer: bytearray | None = None

    def inject(self) -> bool:
        # Simulate only: allocate a tiny buffer, never the full size_mb.
        self._buffer = bytearray(min(int(self.size_mb * 1024), 4096))
        return super().inject()

    def recover(self) -> bool:
        self._buffer = None
        return super().recover()


class DiskFill(Fault):
    fault_type = "disk_fill"

    def __init__(self, target: str = "default", duration: float = 60.0, size_mb: float = 1024.0, path: str = "/tmp/chaos-diskfill", **kw: Any) -> None:
        super().__init__(target, duration, size_mb=size_mb, path=path, **kw)
        self.name = self.fault_type
        self.size_mb = float(size_mb)
        self.path = path


class NetworkPartition(Fault):
    fault_type = "network_partition"

    def __init__(self, target: str = "default", duration: float = 60.0, partition_target: str = "peer", **kw: Any) -> None:
        super().__init__(target, duration, partition_target=partition_target, **kw)
        self.name = self.fault_type
        self.partition_target = partition_target


class DNSFailure(Fault):
    fault_type = "dns_failure"

    def __init__(self, target: str = "default", duration: float = 60.0, hostname: str = "example.com", **kw: Any) -> None:
        super().__init__(target, duration, hostname=hostname, **kw)
        self.name = self.fault_type
        self.hostname = hostname


class DependencyDown(Fault):
    fault_type = "dependency_down"

    def __init__(self, target: str = "default", duration: float = 60.0, dependency_name: str = "database", **kw: Any) -> None:
        super().__init__(target, duration, dependency_name=dependency_name, **kw)
        self.name = self.fault_type
        self.dependency_name = dependency_name


class ClockSkew(Fault):
    fault_type = "clock_skew"

    def __init__(self, target: str = "default", duration: float = 60.0, skew_seconds: float = 300.0, **kw: Any) -> None:
        super().__init__(target, duration, skew_seconds=skew_seconds, **kw)
        self.name = self.fault_type
        self.skew_seconds = float(skew_seconds)


FAULT_REGISTRY: dict[str, type[Fault]] = {
    "kill_process": KillProcess,
    "latency_injection": LatencyInjection,
    "cpu_stress": CPUStress,
    "memory_stress": MemoryStress,
    "disk_fill": DiskFill,
    "network_partition": NetworkPartition,
    "dns_failure": DNSFailure,
    "dependency_down": DependencyDown,
    "clock_skew": ClockSkew,
}


def create_fault(fault_type: str, target: str = "default", duration: float = 60.0, **kwargs: Any) -> Fault:
    """Factory: build a fault by registry name. Raises ValueError on unknown type."""
    key = fault_type.strip().lower().replace("-", "_").replace(" ", "_")
    cls = FAULT_REGISTRY.get(key)
    if cls is None:
        raise ValueError(f"unknown fault type: {fault_type!r}. Known: {sorted(FAULT_REGISTRY)}")
    return cls(target=target, duration=duration, **kwargs)

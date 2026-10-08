"""Daniela Engines - 19 Federated Engines for Autonomous AI Service Management."""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0"

_LAZY: dict[str, str] = {
    # Core engines
    "CoreEngine": "daniela_engines.core",
    "DataSecurityEngine": "daniela_engines.data_security",
    "PerformanceEngine": "daniela_engines.performance",
    "ExperienceEngine": "daniela_engines.experience",
    "AutomationEngine": "daniela_engines.automation",
    # Intelligence engines
    "IntelEngine": "daniela_engines.intel",
    "AutoEngine": "daniela_engines.auto",
    "DataEngine": "daniela_engines.data",
    "SecureEngine": "daniela_engines.secure",
    "DevToolsEngine": "daniela_engines.devtools",
    "EcosystemEngine": "daniela_engines.ecosystem",
    "UXEngine": "daniela_engines.ux",
    "ScaleEngine": "daniela_engines.scale",
    "ChaosEngine": "daniela_engines.chaos",
    "BrandEngine": "daniela_engines.brand",
    "GatewayEngine": "daniela_engines.gateway",
    "OrchestratorEngine": "daniela_engines.orchestrator",
    "InfraOptEngine": "daniela_engines.infra_opt",
    "AgentMobileEngine": "daniela_engines.agent_mobile",
    # Base classes
    "BaseEngine": "daniela_engines.base",
    "EngineRegistry": "daniela_engines.registry",
    "EngineStatus": "daniela_engines.registry",
}

__all__ = [
    "__version__",
    "AgentMobileEngine",
    "AutoEngine",
    "BaseEngine",
    "BrandEngine",
    "ChaosEngine",
    "CoreEngine",
    "DataEngine",
    "DataSecurityEngine",
    "DevToolsEngine",
    "EcosystemEngine",
    "EngineRegistry",
    "EngineStatus",
    "ExperienceEngine",
    "GatewayEngine",
    "InfraOptEngine",
    "IntelEngine",
    "OrchestratorEngine",
    "PerformanceEngine",
    "ScaleEngine",
    "SecureEngine",
    "UXEngine",
]


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        import importlib
        module = importlib.import_module(_LAZY[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
"""A simulation world definition."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Physics(str, Enum):
    MUJOCO = "mujoco"
    ISAAC = "isaac"
    GENESIS = "genesis"


@dataclass
class WorldConfig:
    name: str
    physics: Physics = Physics.MUJOCO
    gravity: float = -9.81
    timestep: float = 0.002
    objects: List[Dict[str, Any]] = field(default_factory=list)
    agents: List[Dict[str, Any]] = field(default_factory=list)


class World:
    """A simulation world (engine-agnostic description)."""

    def __init__(self, config: WorldConfig) -> None:
        self.config = config
        self._step = 0
        self._state: Dict[str, Any] = {}

    def reset(self) -> Dict[str, Any]:
        self._step = 0
        self._state = {
            "world": self.config.name,
            "physics": self.config.physics.value,
            "step": 0,
        }
        return self._state

    def step(self, action: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._step += 1
        self._state["step"] = self._step
        self._state["last_action"] = action or {}
        return self._state

    @property
    def observation(self) -> Dict[str, Any]:
        return dict(self._state)

"""Registry of named simulation worlds."""
from __future__ import annotations

from typing import Dict

from .world import World, WorldConfig, Physics


class WorldRegistry:
    """Create worlds by name from built-in configs."""

    def __init__(self) -> None:
        self._worlds: Dict[str, WorldConfig] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults = [
            WorldConfig(name="empty-room", physics=Physics.MUJOCO),
            WorldConfig(
                name="kitchen",
                physics=Physics.MUJOCO,
                objects=[{"type": "table"}, {"type": "chair"}],
            ),
            WorldConfig(
                name="warehouse",
                physics=Physics.ISAAC,
                agents=[{"type": "mobile_robot"}],
            ),
            WorldConfig(name="humanoid-arena", physics=Physics.ISAAC),
        ]
        for cfg in defaults:
            self._worlds[cfg.name] = cfg

    def create(self, name: str) -> World:
        cfg = self._worlds.get(name)
        if cfg is None:
            raise KeyError(f"unknown world: {name}")
        return World(cfg)

    def list(self) -> list[str]:
        return list(self._worlds.keys())

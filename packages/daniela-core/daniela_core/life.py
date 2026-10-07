"""
Digital Life - Daniela's autonomous daily existence (admin-only surface).

Goals, mood, circadian rhythm, proactive suggestions. Only the admin
can configure or enable these; the rest can only observe.
"""
from __future__ import annotations

import asyncio
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Mood(str, Enum):
    CALM = "calm"
    FOCUSED = "focused"
    ENERGETIC = "energetic"
    REFLECTIVE = "reflective"


@dataclass
class Goal:
    id: str
    title: str
    progress: float = 0.0
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class DigitalLife:
    """Autonomous digital existence: goals, mood, rhythm, proactive nudges."""

    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled
        self.mood = Mood.CALM
        self.goals: dict[str, Goal] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        async with self._lock:
            self.goals.clear()

    async def set_enabled(self, enabled: bool, *, admin: bool = False) -> bool:
        if enabled and not admin:
            raise PermissionError("DigitalLife requires admin privileges to enable")
        self.enabled = enabled
        return self.enabled

    async def add_goal(self, title: str) -> Goal:
        async with self._lock:
            goal = Goal(id=str(uuid.uuid4()), title=title)
            self.goals[goal.id] = goal
            return goal

    async def advance_goal(self, goal_id: str, step: float = 0.1) -> Goal:
        async with self._lock:
            goal = self.goals.get(goal_id)
            if not goal:
                raise KeyError(f"unknown goal {goal_id}")
            goal.progress = min(1.0, goal.progress + step)
            if goal.progress >= 1.0:
                goal.completed = True
            return goal

    async def update_mood(self, now: datetime | None = None) -> Mood:
        """Circadian mood rhythm: energetic midday, calm night."""
        now = now or datetime.utcnow()
        hour = now.hour + now.minute / 60.0
        # sinusoidal energy curve peaking at 14:00
        energy = 0.5 + 0.5 * math.sin(((hour - 8) / 24) * 2 * math.pi)
        if energy > 0.75:
            self.mood = Mood.ENERGETIC
        elif energy > 0.5:
            self.mood = Mood.FOCUSED
        elif energy > 0.25:
            self.mood = Mood.REFLECTIVE
        else:
            self.mood = Mood.CALM
        return self.mood

    async def suggest(self) -> list[dict[str, Any]]:
        """Proactive suggestions based on mood and goals."""
        await self.update_mood()
        suggestions: list[dict[str, Any]] = []
        pending = [g for g in self.goals.values() if not g.completed]
        if pending:
            next_goal = min(pending, key=lambda g: g.progress)
            suggestions.append({
                "type": "goal",
                "text": f"Continue '{next_goal.title}' ({next_goal.progress:.0%})",
            })
        if self.mood == Mood.ENERGETIC:
            suggestions.append({"type": "rhythm", "text": "High energy — good time for deep work."})
        elif self.mood == Mood.CALM:
            suggestions.append({"type": "rhythm", "text": "Calm hour — good time to review memories."})
        return suggestions

    def as_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mood": self.mood.value,
            "goals": len(self.goals),
            "completed": sum(1 for g in self.goals.values() if g.completed),
        }

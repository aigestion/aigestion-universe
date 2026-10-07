"""Unit tests for DigitalLife (admin-gated autonomous existence)."""
from datetime import datetime

import pytest

from life import DigitalLife, Mood


@pytest.fixture
async def life():
    d = DigitalLife()
    await d.initialize()
    yield d
    await d.shutdown()


async def test_disabled_by_default(life):
    assert life.enabled is False


async def test_enable_requires_admin(life):
    with pytest.raises(PermissionError):
        await life.set_enabled(True, admin=False)


async def test_enable_with_admin(life):
    assert await life.set_enabled(True, admin=True) is True


async def test_goal_lifecycle(life):
    goal = await life.add_goal("Learn Rust")
    assert goal.progress == 0.0
    assert goal.completed is False

    goal = await life.advance_goal(goal.id, 0.5)
    assert goal.progress == 0.5
    goal = await life.advance_goal(goal.id, 0.5)
    assert goal.progress == 1.0
    assert goal.completed is True


async def test_advance_unknown_goal(life):
    with pytest.raises(KeyError):
        await life.advance_goal("nope")


async def test_circadian_mood(life):
    midday = datetime(2026, 1, 1, 14, 0)
    mood = await life.update_mood(midday)
    assert mood in (Mood.ENERGETIC, Mood.FOCUSED)

    night = datetime(2026, 1, 1, 3, 0)
    mood = await life.update_mood(night)
    assert mood in (Mood.CALM, Mood.REFLECTIVE)


async def test_suggest_includes_goals(life):
    await life.add_goal("Ship v0.2")
    suggestions = await life.suggest()
    assert any(s["type"] == "goal" for s in suggestions)


async def test_status(life):
    await life.add_goal("g1")
    s = life.as_dict()
    assert s["goals"] == 1
    assert s["completed"] == 0

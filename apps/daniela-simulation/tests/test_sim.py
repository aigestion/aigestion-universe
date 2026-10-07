"""Tests for simulation worlds (registry + stepping)."""
import sys

import pytest

sys.path.insert(0, r"C:\Users\Alejandro\aigestion-universe\apps\daniela-simulation")

from daniela_simulation import WorldRegistry


def test_list_worlds():
    reg = WorldRegistry()
    names = reg.list()
    assert "empty-room" in names
    assert "kitchen" in names
    assert "warehouse" in names
    assert "humanoid-arena" in names


def test_create_and_step():
    reg = WorldRegistry()
    world = reg.create("kitchen")
    state = world.reset()
    assert state["world"] == "kitchen"
    assert state["step"] == 0

    state = world.step({"robot": "move_forward"})
    assert state["step"] == 1
    assert world.observation["last_action"] == {"robot": "move_forward"}


def test_unknown_world():
    reg = WorldRegistry()
    with pytest.raises(KeyError):
        reg.create("nope")

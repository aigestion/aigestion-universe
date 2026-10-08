"""Unit tests for PersonaManager."""

import pytest

from daniela_core.persona import PersonaManager


@pytest.fixture
async def persona():
    p = PersonaManager()
    await p.initialize()
    yield p
    await p.shutdown()


async def test_default_persona(persona):
    d = persona.as_dict()
    assert d["name"] == "Daniela"
    assert d["empathy"] == 0.96
    assert d["coherence_level"] == 4


async def test_rename(persona):
    p = await persona.rename("  aurora  ")
    assert p.name == "Aurora"


async def test_rename_rejects_empty(persona):
    with pytest.raises(ValueError):
        await persona.rename("   ")


async def test_tune_traits(persona):
    p = await persona.tune(empathy=0.8, humor=0.9)
    assert p.empathy == 0.8
    assert p.humor == 0.9
    # untouched stay default
    assert p.creativity == 0.7


async def test_tune_rejects_out_of_range(persona):
    with pytest.raises(ValueError):
        await persona.tune(empathy=1.5)


async def test_greet_uses_name(persona):
    await persona.rename("Vega")
    greeting = await persona.greet()
    assert "Vega" in greeting

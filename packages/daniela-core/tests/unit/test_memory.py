"""Unit tests for MemoryVault (three-tier memory)."""
import pytest

from daniela_core.memory import MemoryVault, Tier


@pytest.fixture
async def vault():
    v = MemoryVault(max_per_tier=100)
    await v.initialize()
    yield v
    await v.shutdown()


async def test_store_and_recall(vault):
    await vault.store(Tier.EPISODIC, "User asked about weather", importance=0.8)
    results = await vault.recall("weather")
    assert len(results) == 1
    assert results[0].tier == Tier.EPISODIC
    assert results[0].access_count == 1  # touched on recall


async def test_recall_tier_filter(vault):
    await vault.store(Tier.EPISODIC, "weather event")
    await vault.store(Tier.SEMANTIC, "weather fact")
    episodic = await vault.recall("weather", tier=Tier.EPISODIC)
    assert len(episodic) == 1
    assert all(m.tier == Tier.EPISODIC for m in episodic)


async def test_recall_limit(vault):
    for i in range(5):
        await vault.store(Tier.EPISODIC, f"weather note {i}")
    results = await vault.recall("weather", limit=2)
    assert len(results) == 2


async def test_consolidate_merges_duplicates(vault):
    await vault.store(Tier.EPISODIC, "Daniela runs on port 9200")
    await vault.store(Tier.EPISODIC, "daniela runs on port 9200")  # duplicate (case-insensitive)
    before = (await vault.recall("port 9200", limit=100)).__len__()
    assert before == 2
    report = await vault.consolidate()
    assert report["merged"] == 1
    after = await vault.recall("port 9200", limit=100)
    assert len(after) == 1


async def test_decay_reduces_stale_importance(vault):
    from datetime import datetime, timedelta
    m = await vault.store(Tier.EPISODIC, "old weather", importance=1.0)
    m.created_at = datetime.utcnow() - timedelta(days=60)
    decayed = await vault.decay(half_life_days=30.0)
    assert decayed == 1
    assert m.importance < 1.0


async def test_eviction_when_full():
    v = MemoryVault(max_per_tier=2)
    await v.initialize()
    await v.store(Tier.EPISODIC, "low", importance=0.1)
    await v.store(Tier.EPISODIC, "high", importance=0.9)
    await v.store(Tier.EPISODIC, "mid", importance=0.5)
    stats = v.stats()
    assert stats["episodic"] == 2
    remaining = await v.recall("", limit=10)
    contents = {m.content for m in remaining}
    assert "low" not in contents  # least-important evicted
    await v.shutdown()


async def test_stats(vault):
    await vault.store(Tier.EPISODIC, "e1")
    await vault.store(Tier.SEMANTIC, "s1")
    await vault.store(Tier.PROCEDURAL, "p1")
    stats = vault.stats()
    assert stats == {"episodic": 1, "semantic": 1, "procedural": 1}

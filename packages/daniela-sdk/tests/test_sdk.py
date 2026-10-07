"""Tests for the Daniela SDK (models + client interface).

Live-method tests (process, memory_store, etc.) require a running
daniela-core; see daniela-core/tests/integration for API coverage.
These tests verify models, defaults, and client construction.
"""
import sys

sys.path.insert(0, r"C:\Users\Alejandro\aigestion-universe\packages\daniela-sdk")

from daniela_sdk import BrainStats, DanielaClient, EngineInfo, MemoryTier
from daniela_sdk.models import MemoryItem, ProcessResult


def test_brain_stats_defaults():
    s = BrainStats()
    assert s.coherence_level == 4
    assert s.empathy_base == 0.96
    assert s.max_nodes == 12480


def test_engine_info():
    e = EngineInfo(engine="core", endpoint="daniela:9200")
    assert e.healthy is True
    assert e.load == 0.0


def test_memory_tier():
    t = MemoryTier(tier="episodic", count=10)
    assert t.count == 10


def test_process_result_defaults():
    r = ProcessResult()
    assert r.coherence == 4
    assert r.empathy == 0.96


def test_memory_item():
    m = MemoryItem(id="x", tier="episodic", content="hi")
    assert m.importance == 0.5
    assert m.access_count == 0


def test_client_construction():
    c = DanielaClient("http://localhost:9200/")
    # trailing slash stripped
    assert str(c._client.base_url) == "http://localhost:9200"
    c.close()


def test_client_with_key():
    c = DanielaClient("http://localhost:9200", api_key="sk-test")
    assert c._client.headers["Authorization"] == "Bearer sk-test"
    c.close()


def test_client_interface():
    c = DanielaClient()
    for method in (
        "process", "brain_stats", "memory_store", "memory_recall",
        "memory_stats", "delegate", "engines", "greet", "rename", "health",
    ):
        assert callable(getattr(c, method)), method
    c.close()

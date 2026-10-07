"""Unit tests for Orchestrator (swarm + Raft consensus)."""
import pytest

from daniela_core.orchestrator import Engine, Orchestrator, TaskStatus


@pytest.fixture
async def orch():
    o = Orchestrator()
    await o.initialize()
    yield o
    await o.shutdown()


async def test_initialize_registers_all_engines(orch):
    assert len(orch.nodes) == len(Engine)
    assert orch._leader == Engine.CORE


async def test_delegate_routes_security(orch):
    task = await orch.delegate("encrypt the vault")
    assert task.engine == Engine.SECURE
    assert task.status == TaskStatus.DELEGATED


async def test_delegate_routes_mobile(orch):
    task = await orch.delegate("deploy to the pixel phone")
    assert task.engine == Engine.AGENT_MOBILE


async def test_delegate_defaults_to_core(orch):
    task = await orch.delegate("do something generic")
    assert task.engine == Engine.CORE


async def test_execute_completes_task(orch):
    task = await orch.delegate("benchmark latency")
    result = await orch.execute(task.id)
    assert result["engine"] == Engine.PERFORMANCE.value
    assert orch.tasks[task.id].status == TaskStatus.COMPLETED


async def test_execute_unknown_task(orch):
    with pytest.raises(KeyError):
        await orch.execute("missing")


async def test_consensus_reaches_quorum(orch):
    report = await orch.consensus({"action": "deploy"})
    assert report["accepted"] is True
    assert report["votes"] >= report["quorum"]


async def test_stats(orch):
    s = orch.stats()
    assert s["nodes"] == len(Engine)
    assert s["healthy"] == len(Engine)

"""Unit tests for Brain, AgentRegistry, VoiceEngine, ToolGateway."""
import pytest

from agents import AgentRegistry, AgentRole
from brain import Brain
from tools import Provider, ToolGateway
from voice import VoiceEngine


async def test_brain_pipeline():
    brain = Brain()
    result = await brain.process("hello", {"source": "test"})
    assert "perception" in result
    assert "reasoning" in result
    assert "decision" in result
    assert "action" in result
    assert result["coherence"] == 4
    assert result["empathy"] == 0.96


async def test_agents_dispatch_and_release():
    reg = AgentRegistry()
    await reg.initialize()
    assert len(reg.list()) >= 6

    agent = await reg.dispatch(AgentRole.CODER)
    assert agent is not None
    assert agent.role == AgentRole.CODER
    assert agent.busy is True

    await reg.release(agent.id)
    agent2 = await reg.dispatch(AgentRole.CODER)
    assert agent2.id == agent.id
    await reg.shutdown()


async def test_agents_dispatch_exhausted():
    reg = AgentRegistry()
    await reg.initialize()
    # Drain all TESTER agents (exactly 1 by default)
    first = await reg.dispatch(AgentRole.TESTER)
    assert first is not None
    second = await reg.dispatch(AgentRole.TESTER)
    assert second is None
    await reg.shutdown()


async def test_voice_synthesize():
    v = VoiceEngine()
    out = await v.synthesize("hello world")
    assert out["text"] == "hello world"
    assert out["voice"] == "daniela"
    assert out["audio_ref"].startswith("tts://")


async def test_voice_list():
    v = VoiceEngine()
    voices = await v.voices()
    assert "daniela" in voices["voices"]


async def test_tools_builtin():
    gw = ToolGateway()
    await gw.initialize()
    tools = gw.list_tools()
    assert "web_search" in tools
    assert "memory_recall" in tools
    await gw.shutdown()


async def test_tools_call_and_providers():
    gw = ToolGateway()
    await gw.initialize()
    result = await gw.call("memory_recall", arguments={"query": "x"})
    assert result.output["query"] == "x"
    assert result.cost_usd == 0.0  # zero markup

    gw.set_key(Provider.OPENAI, "sk-test")
    assert gw.has_key(Provider.OPENAI) is True
    providers = gw.providers()
    assert providers["openai"] is True
    await gw.shutdown()


async def test_tools_unknown():
    gw = ToolGateway()
    await gw.initialize()
    with pytest.raises(KeyError):
        await gw.call("nope")
    await gw.shutdown()

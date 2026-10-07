"""Tests for the EvalHarness (research)."""
import asyncio
import sys

sys.path.insert(0, r"C:\Users\Alejandro\aigestion-universe\apps\daniela-research")

from daniela_research.eval_harness import EvalHarness


def test_empty_summary():
    h = EvalHarness("empty")
    s = h.summary()
    assert s == {"pass_rate": 0.0, "avg_score": 0.0, "avg_latency_ms": 0.0, "n": 0}


def test_perfect_run():
    h = EvalHarness("perfect")
    h.add("2+2?", "4")
    h.add("capital of France?", "Paris")

    async def model(prompt: str) -> str:
        return {"2+2?": "4", "capital of France?": "Paris"}[prompt]

    report = asyncio.run(h.run(model))
    assert report["pass_rate"] == 1.0
    assert report["n"] == 2


def test_partial_run():
    h = EvalHarness("partial")
    h.add("a", "a")
    h.add("b", "b")

    async def model(prompt: str) -> str:
        return "a"  # always answers "a"

    report = asyncio.run(h.run(model))
    assert report["pass_rate"] == 0.5


def test_custom_scorer():
    h = EvalHarness("custom")
    h.add("q", "expected")

    async def model(prompt: str) -> str:
        return "wrong"

    def scorer(expected: str, output: str) -> float:
        return 0.75

    report = asyncio.run(h.run(model, scorer=scorer))
    assert report["avg_score"] == 0.75
    assert report["pass_rate"] == 1.0  # 0.75 >= 0.5

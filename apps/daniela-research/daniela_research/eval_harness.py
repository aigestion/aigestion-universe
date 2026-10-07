"""Eval harness for Daniela OS research experiments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import asyncio
import time


@dataclass
class EvalCase:
    id: str
    prompt: str
    expected: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    score: float
    latency_ms: float
    notes: str = ""


class EvalHarness:
    """Run eval cases against a callable (model, tool, or pipeline)."""

    def __init__(self, name: str = "eval") -> None:
        self.name = name
        self.cases: List[EvalCase] = []
        self.results: List[EvalResult] = []

    def add(self, prompt: str, expected: str, *, case_id: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None) -> None:
        self.cases.append(EvalCase(
            id=case_id or f"case-{len(self.cases)}",
            prompt=prompt,
            expected=expected,
            metadata=metadata or {},
        ))

    async def run(self, fn: Callable[[str], Any],
                  scorer: Optional[Callable[[str, str], float]] = None) -> Dict[str, Any]:
        self.results.clear()
        for case in self.cases:
            start = time.perf_counter()
            output = await _maybe_await(fn(case.prompt))
            latency_ms = (time.perf_counter() - start) * 1000
            score = (scorer(case.expected, output) if scorer
                     else self._default_scorer(case.expected, output))
            self.results.append(EvalResult(
                case_id=case.id,
                passed=score >= 0.5,
                score=score,
                latency_ms=latency_ms,
            ))
        return self.summary()

    def _default_scorer(self, expected: str, output: str) -> float:
        if not expected or not output:
            return 0.0
        exp, out = expected.lower(), output.lower()
        if exp == out:
            return 1.0
        overlap = len(set(exp.split()) & set(out.split()))
        return overlap / max(len(set(exp.split())), 1)

    def summary(self) -> Dict[str, Any]:
        if not self.results:
            return {"pass_rate": 0.0, "avg_score": 0.0, "avg_latency_ms": 0.0, "n": 0}
        n = len(self.results)
        return {
            "pass_rate": sum(1 for r in self.results if r.passed) / n,
            "avg_score": sum(r.score for r in self.results) / n,
            "avg_latency_ms": sum(r.latency_ms for r in self.results) / n,
            "n": n,
        }


async def _maybe_await(value: Any) -> Any:
    if asyncio.iscoroutine(value):
        return await value
    return value

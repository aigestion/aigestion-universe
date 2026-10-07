"""Response models for the Daniela SDK."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class BrainStats(BaseModel):
    coherence_level: int = 4
    empathy_base: float = 0.96
    max_nodes: int = 12480
    nodes: int = 0


class EngineInfo(BaseModel):
    engine: str
    endpoint: str
    healthy: bool = True
    load: float = 0.0


class MemoryTier(BaseModel):
    tier: str
    count: int = 0


class ProcessResult(BaseModel):
    perception: dict = {}
    reasoning: dict = {}
    decision: dict = {}
    action: dict = {}
    coherence: int = 4
    empathy: float = 0.96


class MemoryItem(BaseModel):
    id: str
    tier: str
    content: str
    importance: float = 0.5
    access_count: int = 0

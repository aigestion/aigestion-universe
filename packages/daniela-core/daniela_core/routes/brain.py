"""Brain routes - cognitive processing."""
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class ProcessRequest(BaseModel):
    input: str
    context: dict[str, Any] = {}

class ProcessResponse(BaseModel):
    perception: dict[str, Any]
    reasoning: dict[str, Any]
    decision: dict[str, Any]
    action: dict[str, Any]
    coherence: int
    empathy: float

@router.post("/process", response_model=ProcessResponse)
async def process(req: ProcessRequest, request: Request):
    brain = request.app.state.brain
    result = await brain.process(req.input, req.context)
    return ProcessResponse(**result)

@router.get("/stats")
async def stats(request: Request):
    brain = request.app.state.brain
    return {
        "coherence_level": brain.coherence_level,
        "empathy_base": brain.empathy_base,
        "max_nodes": brain.max_nodes,
        "nodes": len(brain.nodes),
    }

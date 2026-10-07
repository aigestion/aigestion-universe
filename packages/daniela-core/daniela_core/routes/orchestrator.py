"""Orchestrator routes - swarm delegation and Raft consensus."""
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class DelegateRequest(BaseModel):
    description: str
    payload: dict[str, Any] = {}

class ConsensusRequest(BaseModel):
    proposal: dict[str, Any]

@router.post("/delegate")
async def delegate(req: DelegateRequest, request: Request):
    orch = request.app.state.orchestrator
    task = await orch.delegate(req.description, payload=req.payload)
    return {"task_id": task.id, "engine": task.engine.value if task.engine else None,
            "status": task.status.value}

@router.post("/execute/{task_id}")
async def execute(task_id: str, request: Request):
    orch = request.app.state.orchestrator
    result = await orch.execute(task_id)
    return result

@router.post("/consensus")
async def consensus(req: ConsensusRequest, request: Request):
    orch = request.app.state.orchestrator
    return await orch.consensus(req.proposal)

@router.get("/engines")
async def engines(request: Request):
    orch = request.app.state.orchestrator
    return {
        "engines": [
            {"engine": e.value, "endpoint": n.endpoint, "healthy": n.healthy, "load": n.load}
            for e, n in orch.nodes.items()
        ]
    }

@router.get("/stats")
async def stats(request: Request):
    orch = request.app.state.orchestrator
    return orch.stats()

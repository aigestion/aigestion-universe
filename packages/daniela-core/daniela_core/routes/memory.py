"""Memory routes - three-tier memory vault."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from daniela_core.memory import Tier

router = APIRouter()

class StoreRequest(BaseModel):
    tier: Tier
    content: str
    importance: float = 0.5
    metadata: dict = {}
    embedding: list[float] | None = None

class RecallRequest(BaseModel):
    query: str
    tier: Tier | None = None
    limit: int = 10

@router.post("/store")
async def store(req: StoreRequest, request: Request):
    memory = request.app.state.memory
    m = await memory.store(req.tier, req.content, importance=req.importance,
                           metadata=req.metadata, embedding=req.embedding)
    return {"id": m.id, "tier": m.tier.value, "created_at": m.created_at.isoformat()}

@router.post("/recall")
async def recall(req: RecallRequest, request: Request):
    memory = request.app.state.memory
    results = await memory.recall(req.query, tier=req.tier, limit=req.limit)
    return {
        "count": len(results),
        "memories": [
            {"id": m.id, "tier": m.tier.value, "content": m.content,
             "importance": m.importance, "access_count": m.access_count}
            for m in results
        ],
    }

@router.post("/consolidate")
async def consolidate(request: Request):
    memory = request.app.state.memory
    return await memory.consolidate()

@router.post("/decay")
async def decay(request: Request, half_life_days: float = 30.0):
    memory = request.app.state.memory
    decayed = await memory.decay(half_life_days)
    return {"decayed": decayed}

@router.get("/stats")
async def stats(request: Request):
    memory = request.app.state.memory
    return memory.stats()

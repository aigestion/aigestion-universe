"""Vault routes - persistent memory with knowledge graph."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from daniela_core.memory_vault import MemoryVault

router = APIRouter()


class RecordRequest(BaseModel):
    source: str
    content: str = Field(min_length=1)


class RecallRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


class RecientesRequest(BaseModel):
    limite: int = Field(default=20, ge=1, le=200)


def _vault(request: Request) -> MemoryVault:
    return request.app.state.persistent_vault


@router.post("/record")
async def record(req: RecordRequest, request: Request) -> dict[str, Any]:
    if not req.content.strip():
        raise HTTPException(status_code=422, detail="content vacio")
    doc_id = _vault(request).record(req.source, req.content)
    return {"id": doc_id}


@router.post("/recall")
async def recall(req: RecallRequest, request: Request) -> dict[str, Any]:
    memories = _vault(request).recall(req.query, top_k=req.top_k)
    return {"count": len(memories), "memories": memories}


@router.post("/recientes")
async def recientes(req: RecientesRequest, request: Request) -> dict[str, Any]:
    memories = _vault(request).recientes(limite=req.limite)
    return {"count": len(memories), "memories": memories}


@router.delete("/olvidar/{doc_id}")
async def olvidar(doc_id: int, request: Request) -> dict[str, Any]:
    result = _vault(request).olvidar(doc_id)
    if result["docs"] == 0:
        raise HTTPException(status_code=404, detail="recuerdo no encontrado")
    return result


@router.get("/stats")
async def stats(request: Request) -> dict[str, Any]:
    return _vault(request).stats()

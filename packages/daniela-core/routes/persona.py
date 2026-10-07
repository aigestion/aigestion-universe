"""Persona routes - identity and personality."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class RenameRequest(BaseModel):
    name: str

class TuneRequest(BaseModel):
    empathy: float | None = None
    creativity: float | None = None
    formality: float | None = None
    humor: float | None = None

@router.post("/rename")
async def rename(req: RenameRequest, request: Request):
    persona = request.app.state.persona
    p = await persona.rename(req.name)
    return p.as_dict()

@router.post("/tune")
async def tune(req: TuneRequest, request: Request):
    persona = request.app.state.persona
    p = await persona.tune(empathy=req.empathy, creativity=req.creativity,
                           formality=req.formality, humor=req.humor)
    return p.as_dict()

@router.get("/greet")
async def greet(request: Request):
    persona = request.app.state.persona
    return {"greeting": await persona.greet()}

@router.get("/me")
async def me(request: Request):
    persona = request.app.state.persona
    return persona.as_dict()

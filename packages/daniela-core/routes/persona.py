"""Persona routes - identity and personality."""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

if TYPE_CHECKING:
    from persona import PersonaManager

router = APIRouter()


class RenameRequest(BaseModel):
    name: str


class TuneRequest(BaseModel):
    empathy: float | None = None
    creativity: float | None = None
    formality: float | None = None
    humor: float | None = None


@router.post("/rename")
async def rename(req: RenameRequest, request: Request) -> dict[str, Any]:
    persona: PersonaManager = request.app.state.persona
    p = await persona.rename(req.name)
    return p.as_dict()


@router.post("/tune")
async def tune(req: TuneRequest, request: Request) -> dict[str, Any]:
    persona: PersonaManager = request.app.state.persona
    p = await persona.tune(
        empathy=req.empathy, creativity=req.creativity, formality=req.formality, humor=req.humor
    )
    return p.as_dict()


@router.get("/greet")
async def greet(request: Request) -> dict[str, Any]:
    persona: PersonaManager = request.app.state.persona
    return {"greeting": await persona.greet()}


@router.get("/me")
async def me(request: Request) -> dict[str, Any]:
    persona: PersonaManager = request.app.state.persona
    return persona.as_dict()

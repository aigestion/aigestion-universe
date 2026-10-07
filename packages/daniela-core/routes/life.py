"""Digital Life routes - admin-only autonomous existence."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()

class GoalRequest(BaseModel):
    title: str

class EnableRequest(BaseModel):
    enabled: bool
    admin: bool = False

@router.post("/enable")
async def enable(req: EnableRequest, request: Request):
    life = request.app.state.life
    try:
        result = await life.set_enabled(req.enabled, admin=req.admin)
    except PermissionError:
        raise HTTPException(status_code=403, detail="admin required")
    return {"enabled": result}

@router.post("/goals")
async def add_goal(req: GoalRequest, request: Request):
    life = request.app.state.life
    goal = await life.add_goal(req.title)
    return {"id": goal.id, "title": goal.title}

@router.post("/goals/{goal_id}/advance")
async def advance_goal(goal_id: str, request: Request, step: float = 0.1):
    life = request.app.state.life
    try:
        goal = await life.advance_goal(goal_id, step)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown goal")
    return {"id": goal.id, "progress": goal.progress, "completed": goal.completed}

@router.get("/mood")
async def mood(request: Request):
    life = request.app.state.life
    m = await life.update_mood()
    return {"mood": m.value}

@router.get("/suggest")
async def suggest(request: Request):
    life = request.app.state.life
    return {"suggestions": await life.suggest()}

@router.get("/status")
async def status(request: Request):
    life = request.app.state.life
    return life.as_dict()

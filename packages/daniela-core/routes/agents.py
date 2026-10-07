"""Agent registry routes - sub-agent swarm."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agents import AgentRole

router = APIRouter()

class RegisterRequest(BaseModel):
    name: str
    role: AgentRole
    capabilities: list[str] = []

class DispatchRequest(BaseModel):
    role: AgentRole

@router.post("/register")
async def register(req: RegisterRequest, request: Request):
    agents = request.app.state.agents
    agent = await agents.register(req.name, req.role, req.capabilities)
    return agent.as_dict()

@router.post("/dispatch")
async def dispatch(req: DispatchRequest, request: Request):
    agents = request.app.state.agents
    agent = await agents.dispatch(req.role)
    if not agent:
        raise HTTPException(status_code=503, detail="no free agent for role")
    return agent.as_dict()

@router.post("/release/{agent_id}")
async def release(agent_id: str, request: Request):
    agents = request.app.state.agents
    await agents.release(agent_id)
    return {"released": agent_id}

@router.get("/list")
async def list_agents(request: Request):
    agents = request.app.state.agents
    return {"agents": agents.list()}

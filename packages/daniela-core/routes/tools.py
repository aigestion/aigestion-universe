"""Tool gateway routes - BYOK, zero markup, MCP-compatible."""
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from tools import Provider

router = APIRouter()

class RegisterToolRequest(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]

class CallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}
    provider: Provider = Provider.LOCAL

class SetKeyRequest(BaseModel):
    provider: Provider
    key: str

@router.post("/register")
async def register_tool(req: RegisterToolRequest, request: Request):
    tools = request.app.state.tools
    await tools.register_tool(req.name, req.description, req.input_schema)
    return {"registered": req.name}

@router.post("/call")
async def call_tool(req: CallRequest, request: Request):
    tools = request.app.state.tools
    try:
        result = await tools.call(req.name, arguments=req.arguments, provider=req.provider)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown tool")
    return {
        "tool_call_id": result.tool_call_id,
        "output": result.output,
        "tokens_used": result.tokens_used,
        "cost_usd": result.cost_usd,
    }

@router.post("/keys")
async def set_key(req: SetKeyRequest, request: Request):
    tools = request.app.state.tools
    tools.set_key(req.provider, req.key)
    return {"provider": req.provider.value, "configured": True}

@router.get("/list")
async def list_tools(request: Request):
    tools = request.app.state.tools
    return tools.list_tools()

@router.get("/providers")
async def providers(request: Request):
    tools = request.app.state.tools
    return tools.providers()

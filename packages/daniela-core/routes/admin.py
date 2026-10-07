"""Admin routes - protected operations, audit log."""
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class AuditRequest(BaseModel):
    action: str
    actor: str = "admin"
    extra: dict = {}

class RedactRequest(BaseModel):
    text: str

@router.post("/audit")
async def audit(req: AuditRequest, request: Request):
    security = request.app.state.security
    entry = security.audit(req.action, req.actor, extra=req.extra)
    return {
        "seq": entry.seq,
        "timestamp": entry.timestamp,
        "digest": entry.digest,
    }

@router.get("/audit-log")
async def audit_log(request: Request):
    security = request.app.state.security
    return {"entries": security.audit_log(), "chain_valid": security.verify_chain()}

@router.post("/redact")
async def redact(req: RedactRequest, request: Request):
    security = request.app.state.security
    return {"redacted": security.redact(req.text)}

@router.post("/encrypt")
async def encrypt(req: RedactRequest, request: Request):
    security = request.app.state.security
    return security.encrypt(req.text)

@router.get("/status")
async def status(request: Request):
    security = request.app.state.security
    return {
        "algorithm": "AES-256-GCM",
        "audit_entries": len(security.audit_log()),
        "chain_valid": security.verify_chain(),
    }

"""Admin routes - protected operations, audit log."""

import os
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

if TYPE_CHECKING:
    from daniela_core.security import SecurityEngine

router = APIRouter()

# Key slots for the rotation screen. Only presence is ever reported —
# values must NEVER leave the process (no logging, no echo in responses).
KEY_SLOTS: list[dict[str, Any]] = [
    {
        "id": "anthropic",
        "label": "Anthropic",
        "env": ["ANTHROPIC_API_KEY"],
        "dashboard_url": "https://console.anthropic.com/settings/keys",
        "steps": [
            "Open API keys and create a new key.",
            "Update the server .env and restart services.",
            "Verify here, then delete the old key.",
        ],
    },
    {
        "id": "gemini",
        "label": "Google AI / Gemini",
        "env": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "dashboard_url": "https://aistudio.google.com/api-keys",
        "steps": [
            "Create a new key in Google AI Studio (or rotate in Cloud Console).",
            "Update the server .env and restart services.",
            "Verify here, then delete the old key.",
        ],
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "env": ["OPENAI_API_KEY"],
        "dashboard_url": "https://platform.openai.com/api-keys",
        "steps": [
            "Create a new secret key (store it once, it is shown only once).",
            "Update the server .env and restart services.",
            "Verify here, then revoke the old key.",
        ],
    },
    {
        "id": "groq",
        "label": "Groq",
        "env": ["GROQ_API_KEY"],
        "dashboard_url": "https://console.groq.com/keys",
        "steps": [
            "Create a new key and update the server .env.",
            "Restart services and verify here, then delete the old key.",
        ],
    },
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "env": ["OPENROUTER_API_KEY"],
        "dashboard_url": "https://openrouter.ai/settings/keys",
        "steps": [
            "Create a new key and update the server .env.",
            "Restart services and verify here, then delete the old key.",
        ],
    },
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "env": ["DEEPSEEK_API_KEY"],
        "dashboard_url": "https://platform.deepseek.com/api_keys",
        "steps": [
            "Create a new key and update the server .env.",
            "Restart services and verify here, then delete the old key.",
        ],
    },
    {
        "id": "github",
        "label": "GitHub token",
        "env": ["GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"],
        "dashboard_url": "https://github.com/settings/tokens",
        "steps": [
            "Generate a new fine-grained token with minimal scopes.",
            "Update CI secrets / local env and verify here.",
            "Revoke the old token (check its 'Last used' date first).",
        ],
    },
    {
        "id": "jwt",
        "label": "JWT service secret (local)",
        "env": ["AIGESTION_JWT_SECRET", "JWT_SECRET"],
        "dashboard_url": "",
        "steps": [
            'Generate: python -c "import secrets; print(secrets.token_urlsafe(32))".',
            "Set AIGESTION_JWT_SECRET in server .env (never commit it).",
            "Restart services — all sessions/tokens invalidate at once.",
        ],
    },
]


def _slot_status(slot: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": slot["id"],
        "label": slot["label"],
        "env": slot["env"],
        "configured": any(os.getenv(name, "") for name in slot["env"]),
        "dashboard_url": slot["dashboard_url"],
        "steps": slot["steps"],
    }


@router.get("/keys/status")
async def keys_status() -> dict[str, Any]:
    """Presence-only status of API key slots. Never returns secret values."""
    return {"slots": [_slot_status(s) for s in KEY_SLOTS]}


class AuditRequest(BaseModel):
    action: str
    actor: str = "admin"
    extra: dict = {}


class RedactRequest(BaseModel):
    text: str


@router.post("/audit")
async def audit(req: AuditRequest, request: Request) -> dict[str, Any]:
    security: SecurityEngine = request.app.state.security
    entry = security.audit(req.action, req.actor, extra=req.extra)
    return {
        "seq": entry.seq,
        "timestamp": entry.timestamp,
        "digest": entry.digest,
    }


@router.get("/audit-log")
async def audit_log(request: Request) -> dict[str, Any]:
    security: SecurityEngine = request.app.state.security
    return {"entries": security.audit_log(), "chain_valid": security.verify_chain()}


@router.post("/redact")
async def redact(req: RedactRequest, request: Request) -> dict[str, Any]:
    security: SecurityEngine = request.app.state.security
    return {"redacted": security.redact(req.text)}


@router.post("/encrypt")
async def encrypt(req: RedactRequest, request: Request) -> dict[str, Any]:
    security: SecurityEngine = request.app.state.security
    return security.encrypt(req.text)


@router.get("/status")
async def status(request: Request) -> dict[str, Any]:
    security: SecurityEngine = request.app.state.security
    return {
        "algorithm": "AES-256-GCM",
        "audit_entries": len(security.audit_log()),
        "chain_valid": security.verify_chain(),
    }

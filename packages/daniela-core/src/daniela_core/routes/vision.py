"""Vision routes - screenshot analysis for the proactive advisor.

Uses only free paths: the local FreeLLMAPI router when reachable, else
OpenRouter directly with a free vision model (env VISION_MODEL).
Images are never logged or persisted; oversized payloads are rejected.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# 6 MB crudos (base64 infla ~33%): suficiente para 800-1280px utiles.
MAX_IMAGE_BYTES = 6 * 1024 * 1024


class AnalyzeRequest(BaseModel):
    image_b64: str = Field(description="PNG/JPEG en base64, sin prefijo data:")
    prompt: str = Field(
        default="Describe lo que ves en esta captura de pantalla y sugiere "
        "una accion concreta y breve para ayudar al usuario con su tarea.",
        description="Instruccion para el modelo de vision",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto extra (ventana activa, app, objetivo)",
    )


def _post_openai_compatible(
    base_url: str, api_key: str, model: str, messages: list[dict[str, Any]], timeout: float = 90.0
) -> dict[str, Any]:
    data = json.dumps({"model": model, "messages": messages}).encode()
    # base_url sale de env local (FREELLMAPI_URL) o constante https.
    req = urllib.request.Request(  # noqa: S310
        f"{base_url.rstrip('/')}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://aigestion.net",
            "X-Title": "daniela-desktop-advisor",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise HTTPException(
            status_code=502, detail=f"vision upstream [{e.code}]: {body}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"vision upstream unreachable: {e}"
        ) from e


def _extract_text(data: dict[str, Any]) -> str:
    try:
        choice = (data.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content") or ""
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        return content.strip()
    except Exception:
        return ""


@router.post("/analyze")
async def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    try:
        raw = base64.b64decode(req.image_b64, validate=True)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="image_b64 no es base64 valido"
        ) from e
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="imagen demasiado grande (max 6 MB)")

    model = os.getenv("VISION_MODEL", "auto")
    context_txt = (
        f"\nContexto: {json.dumps(req.context)[:500]}" if req.context else ""
    )
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": req.prompt + context_txt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{req.image_b64}"},
                },
            ],
        }
    ]

    # 1) Router local gratis si esta configurado...
    freellmapi_url = os.getenv("FREELLMAPI_URL", "")
    freellmapi_key = os.getenv("FREELLMAPI_KEY", "")
    provider = ""
    if freellmapi_url and freellmapi_key:
        try:
            data = _post_openai_compatible(
                freellmapi_url, freellmapi_key, model, messages
            )
            provider = "freellmapi"
        except HTTPException:
            data = {}
    else:
        data = {}

    # 2) ...si no, OpenRouter directo (modelos :free).
    if not data:
        or_key = os.getenv("OPENROUTER_API_KEY", "")
        if not or_key:
            raise HTTPException(
                status_code=503,
                detail="sin backend de vision: define FREELLMAPI_URL+KEY u OPENROUTER_API_KEY",
            )
        data = _post_openai_compatible(
            "https://openrouter.ai/api/v1", or_key, model, messages
        )
        provider = "openrouter"

    text = _extract_text(data)
    if not text:
        raise HTTPException(status_code=502, detail="el modelo no devolvio texto")
    return {
        "advice": text,
        "provider": provider,
        "model": data.get("model", model),
    }

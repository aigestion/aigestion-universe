"""Voice routes - TTS and STT."""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

if TYPE_CHECKING:
    from voice import VoiceEngine

router = APIRouter()


class SynthesizeRequest(BaseModel):
    text: str
    voice: str | None = None


class TranscribeRequest(BaseModel):
    audio_ref: str
    language: str | None = None


@router.post("/synthesize")
async def synthesize(req: SynthesizeRequest, request: Request) -> dict[str, Any]:
    voice: VoiceEngine = request.app.state.voice
    return await voice.synthesize(req.text, voice=req.voice)


@router.post("/transcribe")
async def transcribe(req: TranscribeRequest, request: Request) -> dict[str, Any]:
    voice: VoiceEngine = request.app.state.voice
    return await voice.transcribe(req.audio_ref, language=req.language)


@router.get("/voices")
async def voices(request: Request) -> dict[str, Any]:
    voice: VoiceEngine = request.app.state.voice
    return await voice.voices()

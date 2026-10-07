"""Voice routes - TTS and STT."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class SynthesizeRequest(BaseModel):
    text: str
    voice: str | None = None

class TranscribeRequest(BaseModel):
    audio_ref: str
    language: str | None = None

@router.post("/synthesize")
async def synthesize(req: SynthesizeRequest, request: Request):
    voice = request.app.state.voice
    return await voice.synthesize(req.text, voice=req.voice)

@router.post("/transcribe")
async def transcribe(req: TranscribeRequest, request: Request):
    voice = request.app.state.voice
    return await voice.transcribe(req.audio_ref, language=req.language)

@router.get("/voices")
async def voices(request: Request):
    voice = request.app.state.voice
    return await voice.voices()

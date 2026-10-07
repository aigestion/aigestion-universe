"""
Voice Engine - On-device TTS and STT for Daniela.

Production uses on-device models (e.g. Piper TTS, Whisper.cpp).
This module defines the interface plus a deterministic fallback.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass
class Speech:
    text: str
    voice: str = "daniela"
    speed: float = 1.0


class VoiceEngine:
    """Text-to-speech and speech-to-text abstraction."""

    def __init__(self, *, voice: str = "daniela", language: str = "en") -> None:
        self.voice = voice
        self.language = language
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        pass

    async def synthesize(self, text: str, *, voice: str | None = None) -> dict[str, Any]:
        """TTS. Returns audio metadata; audio bytes would stream in production."""
        if not self._initialized:
            await self.initialize()
        audio_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return {
            "text": text,
            "voice": voice or self.voice,
            "language": self.language,
            "audio_ref": f"tts://{audio_hash}.wav",
            "duration_hint": max(0.5, len(text) * 0.06),
        }

    async def transcribe(self, audio_ref: str, *, language: str | None = None) -> dict[str, Any]:
        """STT. In production decodes the audio reference; fallback echoes metadata."""
        return {
            "text": "",
            "language": language or self.language,
            "audio_ref": audio_ref,
            "confidence": 0.0,
            "note": "wire to Whisper.cpp / Vosk in production",
        }

    async def voices(self) -> dict[str, Any]:
        return {"voices": [self.voice, "aurora", "neutral"], "language": self.language}

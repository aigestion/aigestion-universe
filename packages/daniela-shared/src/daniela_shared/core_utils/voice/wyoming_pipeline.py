"""
Wyoming Voice Pipeline Integration for Daniela OS
Unified STT → LLM → TTS pipeline using Wyoming protocol.
Supports Whisper.cpp for STT, Piper/Larynx for TTS, and LiteLLM for LLM.
"""
from __future__ import annotations

import json
import subprocess
import uuid
import wave
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx
from wyoming.asr import Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncClient
from wyoming.info import Describe, Info
from wyoming.tts import Synthesize
from wyoming.wake import Detection, NotDetected


class STTEngine(StrEnum):
    """Speech-to-Text engines."""
    WHISPER_CPP = "whisper_cpp"
    FASTER_WHISPER = "faster_whisper"
    VOSK = "vosk"


class TTSEngine(StrEnum):
    """Text-to-Speech engines."""
    PIPER = "piper"
    LARYNX = "larynx"
    COQUI = "coqui"
    EDGE_TTS = "edge_tts"


@dataclass
class VoiceConfig:
    """Voice pipeline configuration."""
    # STT
    stt_engine: STTEngine = STTEngine.WHISPER_CPP
    whisper_model: str = "base"  # tiny, base, small, medium, large
    whisper_cpp_path: str = "whisper-cli"  # or full path
    whisper_language: str = "es"

    # TTS
    tts_engine: TTSEngine = TTSEngine.PIPER
    piper_model: str = "es_ES-sharvard-medium"
    piper_speaker: int | None = None

    # LLM (via LiteLLM)
    llm_base_url: str = "http://localhost:4000/v1"
    llm_api_key: str = "sk-aig-master-key"
    llm_model: str = "openrouter-free"
    llm_system_prompt: str = "Eres Daniela, una asistente inteligente útil y empática."

    # Audio
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024

    # Wyoming satellite (for distributed voice)
    satellite_enabled: bool = False
    satellite_host: str = "localhost"
    satellite_port: int = 10300


@dataclass
class VoiceSession:
    """Active voice session state."""
    session_id: str
    stt_client: AsyncClient | None = None
    tts_client: AsyncClient | None = None
    wake_client: AsyncClient | None = None
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    is_listening: bool = False
    language: str = "es"


class WyomingPipeline:
    """
    Wyoming protocol voice pipeline for Daniela.
    Handles STT → LLM → TTS flow with support for wake word detection.
    """

    def __init__(self, config: VoiceConfig | None = None):
        self.config = config or VoiceConfig()
        self.sessions: dict[str, VoiceSession] = {}
        self._stt_process: subprocess.Popen | None = None
        self._tts_process: subprocess.Popen | None = None

    async def start(self) -> None:
        """Start the voice pipeline services."""
        await self._start_stt_service()
        await self._start_tts_service()

    async def stop(self) -> None:
        """Stop all voice services."""
        if self._stt_process:
            self._stt_process.terminate()
        if self._tts_process:
            self._tts_process.terminate()

    async def _start_stt_service(self) -> None:
        """Start Whisper.cpp as Wyoming ASR service."""
        if self.config.stt_engine == STTEngine.WHISPER_CPP:
            # Whisper.cpp with Wyoming support
            cmd = [
                self.config.whisper_cpp_path,
                "-m", f"models/ggml-{self.config.whisper_model}.bin",
                "-l", self.config.whisper_language,
                "--wyoming",
                "--port", "10301",
            ]
            self._stt_process = subprocess.Popen(cmd)

    async def _start_tts_service(self) -> None:
        """Start Piper as Wyoming TTS service."""
        if self.config.tts_engine == TTSEngine.PIPER:
            # Piper with Wyoming support
            cmd = [
                "piper",
                "--model", self.config.piper_model,
                "--wyoming",
                "--port", "10302",
            ]
            if self.config.piper_speaker is not None:
                cmd.extend(["--speaker", str(self.config.piper_speaker)])
            self._tts_process = subprocess.Popen(cmd)

    async def create_session(self, session_id: str | None = None) -> VoiceSession:
        """Create a new voice session."""
        sid = session_id or str(uuid.uuid4())
        session = VoiceSession(session_id=sid, language=self.config.whisper_language)
        self.sessions[sid] = session
        return session

    async def process_audio_stream(
        self,
        session_id: str,
        audio_stream: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[str, None]:
        """
        Process streaming audio: STT → LLM → TTS.
        Yields transcript chunks and TTS audio.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Connect to STT service
        async with AsyncClient.from_uri("tcp://localhost:10301") as client:
            session.stt_client = client

            # Send audio start
            await client.write_event(AudioStart(
                rate=self.config.sample_rate,
                width=2,
                channels=self.config.channels,
            ).event())

            # Stream audio to STT
            async for chunk in audio_stream:
                await client.write_event(AudioChunk(
                    audio=chunk,
                    rate=self.config.sample_rate,
                    width=2,
                    channels=self.config.channels,
                ).event())

                # Check for transcript
                event = await client.read_event()
                if event and Transcript.is_type(event.type):
                    transcript = Transcript.from_event(event)
                    if transcript.text:
                        # Process through LLM
                        async for response_chunk in self._process_llm(
                            session, transcript.text
                        ):
                            yield response_chunk

            await client.write_event(AudioStop().event())

    async def _process_llm(
        self,
        session: VoiceSession,
        user_text: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process user text through LLM and generate TTS."""
        # Add to conversation history
        session.conversation_history.append({"role": "user", "content": user_text})

        # Keep history manageable
        if len(session.conversation_history) > 20:
            session.conversation_history = session.conversation_history[-20:]

        # Call LLM via LiteLLM
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{self.config.llm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.llm_model,
                    "messages": [
                        {"role": "system", "content": self.config.llm_system_prompt},
                        *session.conversation_history,
                    ],
                    "stream": True,
                },
                timeout=60.0,
            )

            # Stream LLM response
            llm_text = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            llm_text += content
                            yield {"type": "llm_chunk", "text": content}
                    except json.JSONDecodeError:
                        pass

            # Add to history
            session.conversation_history.append({"role": "assistant", "content": llm_text})

            # Generate TTS for complete response
            if llm_text.strip():
                async for audio_chunk in self._synthesize_tts(llm_text):
                    yield {"type": "tts_audio", "audio": audio_chunk}

    async def _synthesize_tts(self, text: str) -> AsyncGenerator[bytes, None]:
        """Synthesize text to speech via Wyoming TTS."""
        async with AsyncClient.from_uri("tcp://localhost:10302") as client:
            await client.write_event(Synthesize(text=text).event())

            async for event in client.read_events():
                if event.type == "audio-chunk":
                    chunk = AudioChunk.from_event(event)
                    yield chunk.audio
                elif event.type == "audio-stop":
                    break

    async def synthesize_file(self, text: str, output_path: Path) -> Path:
        """Synthesize text to audio file."""
        audio_data = b""
        async for chunk in self._synthesize_tts(text):
            audio_data += chunk

        # Save as WAV
        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(audio_data)

        return output_path

    async def detect_wake_word(self, audio_stream: AsyncGenerator[bytes, None]) -> bool:
        """Detect wake word from audio stream."""
        if not self.config.satellite_enabled:
            return False

        async with AsyncClient.from_uri(
            f"tcp://{self.config.satellite_host}:{self.config.satellite_port}"
        ) as client:
            await client.write_event(AudioStart(
                rate=self.config.sample_rate,
                width=2,
                channels=self.config.channels,
            ).event())

            async for chunk in audio_stream:
                await client.write_event(AudioChunk(
                    audio=chunk,
                    rate=self.config.sample_rate,
                    width=2,
                    channels=self.config.channels,
                ).event())

                event = await client.read_event()
                if event and Detection.is_type(event.type):
                    return True
                elif event and NotDetected.is_type(event.type):
                    continue

            await client.write_event(AudioStop().event())
            return False

    def transcribe_file(self, audio_path: Path) -> str:
        """Transcribe audio file using Whisper.cpp (blocking)."""
        if self.config.stt_engine != STTEngine.WHISPER_CPP:
            raise NotImplementedError("File transcription only for whisper_cpp")

        cmd = [
            self.config.whisper_cpp_path,
            "-m", f"models/ggml-{self.config.whisper_model}.bin",
            "-f", str(audio_path),
            "-l", self.config.whisper_language,
            "-otxt",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip()


class WyomingSatellite:
    """
    Wyoming Satellite for distributed voice.
    Runs on Pixel/edge devices, streams audio to central server.
    """

    def __init__(
        self,
        server_uri: str = "tcp://localhost:10300",
        device_name: str = "pixel",
    ):
        self.server_uri = server_uri
        self.device_name = device_name
        self.client: AsyncClient | None = None

    async def connect(self) -> None:
        """Connect to Wyoming server."""
        self.client = await AsyncClient.from_uri(self.server_uri)

        # Send info
        await self.client.write_event(Describe().event())
        event = await self.client.read_event()
        if event and Info.is_type(event.type):
            info = Info.from_event(event)
            print(f"Connected to Wyoming server: {info}")

    async def stream_audio(self, audio_stream: AsyncGenerator[bytes, None]) -> None:
        """Stream audio to server."""
        if not self.client:
            await self.connect()

        await self.client.write_event(AudioStart(
            rate=16000, width=2, channels=1,
        ).event())

        async for chunk in audio_stream:
            await self.client.write_event(AudioChunk(
                audio=chunk, rate=16000, width=2, channels=1,
            ).event())

        await self.client.write_event(AudioStop().event())

    async def receive_audio(self) -> AsyncGenerator[bytes, None]:
        """Receive TTS audio from server."""
        if not self.client:
            await self.connect()

        async for event in self.client.read_events():
            if event.type == "audio-chunk":
                chunk = AudioChunk.from_event(event)
                yield chunk.audio
            elif event.type == "audio-stop":
                break


# Convenience functions for simple usage
async def transcribe_audio(audio_path: Path, model: str = "base") -> str:
    """Quick transcribe using Whisper.cpp."""
    cmd = ["whisper-cli", "-m", f"models/ggml-{model}.bin", "-f", str(audio_path), "-otxt"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


async def synthesize_speech(text: str, output_path: Path, model: str = "es_ES-sharvard-medium") -> Path:
    """Quick TTS using Piper."""
    cmd = ["piper", "--model", model, "--output_file", str(output_path)]
    subprocess.run(cmd, input=text, capture_output=True, text=True)
    return output_path


# Integration with Daniela's existing voice system
class DanielaVoice:
    """High-level voice interface for Daniela."""

    def __init__(self, config: VoiceConfig | None = None):
        self.pipeline = WyomingPipeline(config)
        self.default_session: VoiceSession | None = None

    async def start(self) -> None:
        """Start voice pipeline."""
        await self.pipeline.start()
        self.default_session = await self.pipeline.create_session("daniela_main")

    async def stop(self) -> None:
        """Stop voice pipeline."""
        await self.pipeline.stop()

    async def listen_and_respond(
        self,
        audio_stream: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Listen to audio and generate response."""
        async for event in self.pipeline.process_audio_stream(
            self.default_session.session_id,
            audio_stream,
        ):
            yield event

    async def say(self, text: str) -> bytes:
        """Speak text and return audio."""
        audio_data = b""
        async for chunk in self.pipeline._synthesize_tts(text):
            audio_data += chunk
        return audio_data

    async def say_to_file(self, text: str, output_path: Path) -> Path:
        """Speak text to file."""
        return await self.pipeline.synthesize_file(text, output_path)

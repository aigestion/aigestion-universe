#!/usr/bin/env python3
"""
PA-08: Voice Pipeline Unificado - PC + Pixel same code
=========================================================
Un solo pipeline de voz que detecta el dispositivo y usa el backend correcto.

PC:
  - TTS: edge-tts (gratis, voces Microsoft Neural, 5 voces espanolas)
  - STT: faster-whisper (local, gratis, modelo small/base)
  - Fallback STT: Gemini API (free tier, 15 RPM)

Pixel (Termux):
  - TTS: termux-tts-speak (Android TTS engine)
  - STT: termux-speech-to-text (Google speech recognizer)

Elimina codigo duplicado entre:
  - copiloto_voz.py (Pixel: termux-speech-to-text + termux-tts-speak)
  - daemon_escucha.py (Pixel: termux-speech-to-text only)
  - daniela_satellite_ai.py (PC: edge-tts + genai)

Rutas en daniela_os.py:
  - POST /api/voice/speak    (texto -> voz)
  - POST /api/voice/listen    (escuchar -> texto)
  - GET  /api/voice/status    (estado del pipeline)
  - POST /api/voice/converse  (loop conversacional)

Coste: $0/mes (edge-tts + faster-whisper + Gemini free tier)
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from typing import Callable, Dict, Optional

# ── Optional deps ─────────────────────────────────────────────
# Detect with importlib.util.find_spec (no spurious ImportError, faster than
# try/except ImportError). edge_tts is still imported at module level when
# available so the nested _generate() coroutine inside _speak_pc() can reach
# it; a local import inside _init_engines() would leave it undefined in that
# scope (NameError when _generate() runs).
_EDGE_TTS_AVAILABLE = importlib.util.find_spec("edge_tts") is not None
if _EDGE_TTS_AVAILABLE:
    import edge_tts
else:
    edge_tts = None


# ── Config ───────────────────────────────────────────────────

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "voice_pipeline")
STATE_FILE = os.path.join(STATE_DIR, "voice_pipeline_state.json")

# PC TTS config
PC_TTS_VOICE = "es-ES-ElviraNeural"  # Microsoft Neural, gratis
PC_TTS_RATE = "+0%"
PC_TTS_PITCH = "+0Hz"

# PC STT config
WHISPER_MODEL = "base"  # tiny/base/small/medium (base = good balance)

# Available Spanish voices for edge-tts
PC_VOICES = {
    "elvira": "es-ES-ElviraNeural",  # Female, warm
    "alvaro": "es-ES-AlvaroNeural",  # Male, neutral
    "ximena": "es-MX-XimenaNeural",  # Female, Mexican
    "dalia": "es-MX-DaliaNeural",  # Female, Mexican
    "jorge": "es-ES-JorgeNeural",  # Male, deep
}

# Pixel TTS
PIXEL_TTS_LANG = "es"

# ── Device detection (inline, no import dependency) ───────────


def _is_pixel() -> bool:
    """Detect if running on Pixel (Termux)."""
    if os.path.exists("/data/data/com.termux"):
        return True
    if os.environ.get("TERMUX_VERSION"):
        return True
    if os.environ.get("PREFIX", "").startswith("/data/data/com.termux"):
        return True
    return False


# ── Data classes ──────────────────────────────────────────────


@dataclass
class VoiceState:
    device: str = "pc"
    tts_engine: str = "edge-tts"
    stt_engine: str = "faster-whisper"
    tts_available: bool = False
    stt_available: bool = False
    speak_count: int = 0
    listen_count: int = 0
    last_spoken: str = ""
    last_heard: str = ""
    last_activity: float = 0.0


# ── Unified Voice Pipeline ────────────────────────────────────


class VoicePipeline:
    """Single voice pipeline that works on both PC and Pixel."""

    def __init__(self):
        self._state = VoiceState()
        self._lock = threading.Lock()
        self._edge_tts_ok = False
        self._whisper_ok = False
        self._init_engines()

    def _init_engines(self):
        if _is_pixel():
            self._state.device = "pixel"
            self._state.tts_engine = "termux-tts-speak"
            self._state.stt_engine = "termux-speech-to-text"
            # Check termux commands
            self._state.tts_available = shutil.which("termux-tts-speak") is not None
            self._state.stt_available = shutil.which("termux-speech-to-text") is not None
        else:
            self._state.device = "pc"
            self._state.tts_engine = "edge-tts"
            self._state.stt_engine = "faster-whisper"
            # edge_tts was imported at module level — just reference it here
            self._edge_tts_ok = _EDGE_TTS_AVAILABLE
            self._state.tts_available = _EDGE_TTS_AVAILABLE
            # Check faster-whisper
            self._whisper_ok = importlib.util.find_spec("faster_whisper") is not None
            self._state.stt_available = self._whisper_ok

    # ── TTS: speak() ──────────────────────────────────────────

    def speak(self, text: str, voice: str = "") -> Dict:
        """Speak text using the appropriate TTS engine.

        Args:
            text: Text to speak
            voice: Voice name (PC: elvira/alvaro/ximena/dalia/jorge, Pixel: ignored)
        """
        if not text.strip():
            return {"ok": False, "error": "Empty text"}

        # Sanitize text
        safe = text[:1000].replace("\n", " ").strip()
        if not safe:
            return {"ok": False, "error": "No valid text"}

        if self._state.device == "pixel":
            return self._speak_pixel(safe)
        else:
            return self._speak_pc(safe, voice)

    def _speak_pc(self, text: str, voice: str) -> Dict:
        """PC TTS via edge-tts."""
        if not self._edge_tts_ok:
            return {"ok": False, "error": "edge-tts not installed. pip install edge-tts"}

        voice_id = PC_VOICES.get(voice.lower(), PC_TTS_VOICE)

        try:
            # Generate audio file
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=STATE_DIR)
            tmp.close()
            os.makedirs(STATE_DIR, exist_ok=True)

            async def _generate():
                if edge_tts is None:
                    raise RuntimeError("edge-tts not installed")
                communicate = edge_tts.Communicate(
                    text,
                    voice_id,
                    rate=PC_TTS_RATE,
                    pitch=PC_TTS_PITCH,
                )
                await communicate.save(tmp.name)

            asyncio.run(_generate())

            # Play audio
            self._play_audio_pc(tmp.name)

            with self._lock:
                self._state.speak_count += 1
                self._state.last_spoken = text[:100]
                self._state.last_activity = time.time()

            # Cleanup
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

            return {"ok": True, "engine": "edge-tts", "voice": voice_id}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    def synthesize(self, text: str, voice: str = "") -> dict:
        """Generate TTS audio file WITHOUT playing it.

        Returns {"ok": True, "path": <mp3>, "engine", "voice"} so a frontend
        can fetch the audio and sync the avatar's mouth with it
        (DanielaAvatar.speakAudio). Uses edge-tts on PC and on Pixel too
        when the package is installed (only needs internet to Microsoft);
        otherwise fails and the caller falls back to device speech.

        Files are cached by text+voice hash in STATE_DIR (mp3 are tiny and
        repeated replies cost zero). Entries older than 7 days are pruned.
        """
        if not text or not text.strip():
            return {"ok": False, "error": "Empty text"}
        safe = text[:1000].replace("\n", " ").strip()
        if not safe:
            return {"ok": False, "error": "No valid text"}
        if not _EDGE_TTS_AVAILABLE:
            return {"ok": False, "error": "edge-tts not installed. pip install edge-tts"}

        import hashlib

        voice_id = PC_VOICES.get((voice or "").lower(), PC_TTS_VOICE)
        try:
            os.makedirs(STATE_DIR, exist_ok=True)
            key = hashlib.sha256(f"{voice_id}|{safe}".encode()).hexdigest()[:16]
            path = os.path.join(STATE_DIR, f"tts_{key}.mp3")
            if not (os.path.exists(path) and os.path.getsize(path) > 1024):
                async def _generate():
                    if edge_tts is None:
                        raise RuntimeError("edge-tts not installed")
                    communicate = edge_tts.Communicate(
                        safe,
                        voice_id,
                        rate=PC_TTS_RATE,
                        pitch=PC_TTS_PITCH,
                    )
                    await communicate.save(path)

                asyncio.run(_generate())
            self._limpiar_cache_tts()
            with self._lock:
                self._state.speak_count += 1
                self._state.last_spoken = safe[:100]
                self._state.last_activity = time.time()
            return {"ok": True, "engine": "edge-tts", "voice": voice_id, "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _limpiar_cache_tts(self, max_dias: int = 7) -> None:
        """Prune cached TTS mp3 older than `max_dias`."""
        try:
            ahora = time.time()
            for nombre in os.listdir(STATE_DIR):
                if not (nombre.startswith("tts_") and nombre.endswith(".mp3")):
                    continue
                ruta = os.path.join(STATE_DIR, nombre)
                if ahora - os.path.getmtime(ruta) > max_dias * 86400:
                    os.unlink(ruta)
        except OSError:
            pass

    def _speak_pixel(self, text: str) -> Dict:
        """Pixel TTS via termux-tts-speak."""
        # Sanitize for termux (no special chars that could break the command)
        safe_text = text.replace("'", "").replace('"', "").replace("`", "")

        try:
            result = subprocess.run(
                ["termux-tts-speak", "-l", PIXEL_TTS_LANG, safe_text],
                capture_output=True,
                timeout=15,
            )
            if result.returncode == 0:
                with self._lock:
                    self._state.speak_count += 1
                    self._state.last_spoken = text[:100]
                    self._state.last_activity = time.time()
                return {"ok": True, "engine": "termux-tts-speak"}
            return {"ok": False, "error": result.stderr.decode("utf-8", errors="ignore")}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "TTS timeout (15s)"}
        except FileNotFoundError:
            return {"ok": False, "error": "termux-tts-speak not found"}

    def _play_audio_pc(self, filepath: str):
        """Play an audio file on PC (Windows)."""
        try:
            # Use Windows default player (non-blocking)
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()",
                ],
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass  # Audio playback is best-effort

    # ── STT: listen() ─────────────────────────────────────────

    def listen(self, timeout: int = 10) -> Dict:
        """Listen to microphone and return transcribed text."""
        if self._state.device == "pixel":
            return self._listen_pixel(timeout)
        else:
            return self._listen_pc(timeout)

    def _listen_pc(self, timeout: int) -> Dict:
        """PC STT via faster-whisper (or Gemini API fallback)."""
        if not self._whisper_ok:
            return {
                "ok": False,
                "error": "faster-whisper not installed. pip install faster-whisper",
            }

        try:
            import wave

            import pyaudio  # type: ignore
            from faster_whisper import WhisperModel

            # Record audio
            chunk = 1024
            sample_format = pyaudio.paInt16
            channels = 1
            fs = 16000
            record_seconds = min(timeout, 10)

            p = pyaudio.PyAudio()
            stream = p.open(
                format=sample_format,
                channels=channels,
                rate=fs,
                frames_per_buffer=chunk,
                input=True,
            )
            frames = []
            for _ in range(int(fs / chunk * record_seconds)):
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            p.terminate()

            # Save to temp WAV
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=STATE_DIR)
            tmp.close()
            os.makedirs(STATE_DIR, exist_ok=True)
            wf = wave.open(tmp.name, "wb")
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b"".join(frames))
            wf.close()

            # Transcribe
            model = WhisperModel(WHISPER_MODEL, device="cpu")
            segments, _ = model.transcribe(tmp.name, language="es")
            text = " ".join(seg.text for seg in segments).strip()

            try:
                os.unlink(tmp.name)
            except OSError:
                pass

            with self._lock:
                self._state.listen_count += 1
                self._state.last_heard = text[:100]
                self._state.last_activity = time.time()

            return {"ok": True, "engine": "faster-whisper", "text": text}

        except ImportError as e:
            return {"ok": False, "error": f"Missing dependency: {e}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _listen_pixel(self, timeout: int) -> Dict:
        """Pixel STT via termux-speech-to-text."""
        try:
            result = subprocess.run(
                ["termux-speech-to-text"],
                capture_output=True,
                text=True,
                timeout=max(timeout, 5),
            )
            if result.returncode == 0:
                text = result.stdout.strip()
                with self._lock:
                    self._state.listen_count += 1
                    self._state.last_heard = text[:100]
                    self._state.last_activity = time.time()
                return {"ok": True, "engine": "termux-speech-to-text", "text": text}
            return {"ok": False, "error": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "STT timeout"}
        except FileNotFoundError:
            return {"ok": False, "error": "termux-speech-to-text not found"}

    # ── Conversation loop ─────────────────────────────────────

    def conversation_loop(self, handler: Callable[[str], str], max_turns: int = 10) -> Dict:
        """Run a conversation loop: listen -> process -> speak.

        Args:
            handler: Function that takes user text and returns response text
            max_turns: Maximum conversation turns
        """
        turns = 0
        transcript = []

        for _ in range(max_turns):
            turns += 1
            # Listen
            listen_result = self.listen(timeout=8)
            if not listen_result.get("ok"):
                continue

            user_text = listen_result.get("text", "").strip()
            if not user_text:
                continue

            # Check for exit commands
            if user_text.lower() in ("salir", "terminar", "adios", "exit", "quit", "stop"):
                self.speak("Hasta luego.")
                break

            transcript.append({"role": "user", "text": user_text})

            # Process
            try:
                response = handler(user_text)
            except Exception as e:
                response = f"Error procesando: {e}"

            if not response:
                response = "No entendi, puedes repetir?"

            # Speak response
            self.speak(response)
            transcript.append({"role": "assistant", "text": response})

        return {"ok": True, "turns": turns, "transcript": transcript}

    # ── State ────────────────────────────────────────────────

    def get_state(self) -> Dict:
        with self._lock:
            return asdict(self._state)

    def get_voices(self) -> Dict:
        if self._state.device == "pc":
            return {"device": "pc", "voices": PC_VOICES}
        return {"device": "pixel", "voices": {"default": "termux-tts-speak (Android TTS)"}}

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.get_state(), f, indent=2, ensure_ascii=False)


# ── Singleton ─────────────────────────────────────────────────

_instance: Optional[VoicePipeline] = None


def get_instance() -> VoicePipeline:
    global _instance
    if _instance is None:
        _instance = VoicePipeline()
    return _instance


# ── Flask route registration ──────────────────────────────────


def register_voice_routes(flask_app):
    """Register unified voice pipeline routes in daniela_os.py."""
    from flask import jsonify, request, send_file  # local: sin depender de flask

    @flask_app.route("/api/voice/speak", methods=["POST"])
    def voice_speak():
        data = request.json or {}
        text = data.get("text", "")
        voice = data.get("voice", "")
        return jsonify(get_instance().speak(text, voice))

    @flask_app.route("/api/voice/listen", methods=["POST"])
    def voice_listen():
        data = request.json or {}
        timeout = data.get("timeout", 10)
        return jsonify(get_instance().listen(int(timeout)))

    @flask_app.route("/api/voice/status")
    def voice_status():
        return jsonify(get_instance().get_state())

    @flask_app.route("/api/voice/voices")
    def voice_voices():
        return jsonify(get_instance().get_voices())

    @flask_app.route("/api/voice/tts", methods=["POST"])
    def voice_tts():
        """Synthesize TTS WITHOUT playing: returns the mp3 for the avatar.

        The frontend fetches this and calls DanielaAvatar.speakAudio(url) so
        the mouth moves with the real voice. Speak errors -> 503 JSON (the
        frontend falls back to device speech).
        """
        data = request.json or {}
        res = get_instance().synthesize(data.get("text", ""), data.get("voice", ""))
        if not res.get("ok"):
            return jsonify(res), 503
        return send_file(res["path"], mimetype="audio/mpeg")

    print(
        "[Voice Pipeline] Routes registered: /api/voice/speak, /voice/listen, "
        "/voice/status, /voice/voices, /api/voice/tts"
    )


# ── CLI ───────────────────────────────────────────────────────


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python voice_pipeline.py [status|speak <text>|listen|voices]")
        return

    cmd = sys.argv[1]
    pipeline = get_instance()

    if cmd == "status":
        print(json.dumps(pipeline.get_state(), indent=2))
    elif cmd == "speak":
        text = " ".join(sys.argv[2:]) or "Hola, soy Daniela. Prueba del pipeline de voz unificado."
        result = pipeline.speak(text)
        print(json.dumps(result, indent=2))
    elif cmd == "listen":
        print("Listening...")
        result = pipeline.listen(timeout=5)
        print(json.dumps(result, indent=2))
    elif cmd == "voices":
        print(json.dumps(pipeline.get_voices(), indent=2))
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
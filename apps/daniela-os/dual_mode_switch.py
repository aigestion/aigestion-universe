#!/usr/bin/env python3
"""
Dual-Mode Auto-Switch (PA-06)
=============================
Detecta automaticamente si Daniela esta corriendo en el Pixel (Termux)
o en el PC, y cambia el comportamiento sin codigo separado.

  - En Pixel: TTS nativo Android, haptic, GPS, menos polling
  - En PC: edge-tts, Whisper local, mas recursos, streaming
  - Transicion seamless: mismo codigo, diferente backend

Tambien sincroniza estado entre PC y Pixel via el Pixel Bridge Hub.

Cost: $0 — solo deteccion de plataforma + config
"""

import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
STATE_DIR = PROJECT_ROOT / "data" / "dual_mode"
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "dual_mode_state.json"


@dataclass
class DeviceProfile:
    """Perfil de comportamiento para un dispositivo."""

    device: str  # "pc" or "pixel"
    tts_engine: str  # "edge-tts" or "termux-tts"
    stt_engine: str  # "whisper" or "termux-stt"
    poll_interval: int  # seconds between polls
    features: list  # enabled features
    battery_aware: bool  # adjust based on battery
    streaming: bool  # sensor streaming enabled
    geofence: bool  # geofence detection enabled


PC_PROFILE = DeviceProfile(
    device="pc",
    tts_engine="edge-tts",
    stt_engine="whisper",
    poll_interval=30,
    features=["rag", "deep_analysis", "code_generation", "video_generation", "full_dashboard"],
    battery_aware=False,
    streaming=True,
    geofence=False,
)

PIXEL_PROFILE = DeviceProfile(
    device="pixel",
    tts_engine="termux-tts",
    stt_engine="termux-stt",
    poll_interval=60,
    features=["gps", "camera", "notifications", "haptic", "voice_assistant"],
    battery_aware=True,
    streaming=False,
    geofence=True,
)

PIXEL_LOW_BATTERY_PROFILE = DeviceProfile(
    device="pixel",
    tts_engine="text",  # no TTS to save battery
    stt_engine="disabled",
    poll_interval=300,  # 5 min
    features=["notifications_only", "emergency_alerts"],
    battery_aware=True,
    streaming=False,
    geofence=False,
)


class DualModeSwitch:
    """Auto-deteccion y switch entre PC y Pixel."""

    def __init__(self):
        self._device: str | None = None
        self._profile: DeviceProfile | None = None
        self._battery_pct: int = 100
        self._detected_at: str = ""
        self._load_state()

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self._device = data.get("device")
                self._battery_pct = data.get("battery_pct", 100)
                self._detected_at = data.get("detected_at", "")
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_state(self):
        data = {
            "device": self._device,
            "battery_pct": self._battery_pct,
            "detected_at": self._detected_at,
            "updated_at": datetime.now().isoformat(),
        }
        STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def detect_device(self) -> str:
        """Detecta si estamos en PC o Pixel."""
        # Check 1: Termux path existe
        if os.path.exists("/data/data/com.termux"):
            self._device = "pixel"
        # Check 2: TERMUX_VERSION env var
        elif os.environ.get("TERMUX_VERSION"):
            self._device = "pixel"
        # Check 3: prefix path
        elif sys.prefix.startswith("/data/data/com.termux"):
            self._device = "pixel"
        # Check 4: TERMUX env
        elif os.environ.get("PREFIX", "").startswith("/data/data/com.termux"):
            self._device = "pixel"
        else:
            self._device = "pc"

        self._detected_at = datetime.now().isoformat()
        self._save_state()
        return self._device

    def get_profile(self, force_battery_pct: int | None = None) -> DeviceProfile:
        """Retorna el perfil activo basado en el dispositivo y bateria."""
        if not self._device:
            self.detect_device()

        if force_battery_pct is not None:
            self._battery_pct = force_battery_pct

        if self._device == "pixel":
            if self._battery_pct < 20:
                self._profile = PIXEL_LOW_BATTERY_PROFILE
            else:
                self._profile = PIXEL_PROFILE
        else:
            self._profile = PC_PROFILE

        return self._profile

    def is_pixel(self) -> bool:
        """True si estamos corriendo en el Pixel."""
        if not self._device:
            self.detect_device()
        return self._device == "pixel"

    def is_pc(self) -> bool:
        """True si estamos en el PC."""
        if not self._device:
            self.detect_device()
        return self._device == "pc"

    def update_battery(self, pct: int):
        """Actualiza el nivel de bateria y re-evaluacion del perfil."""
        self._battery_pct = max(0, min(100, pct))
        self._save_state()
        # Re-evaluacion del perfil si cambio el modo
        old_profile = self._profile
        new_profile = self.get_profile()
        if old_profile and new_profile.tts_engine != old_profile.tts_engine:
            return True  # perfil cambio
        return False

    def speak(self, text: str) -> str:
        """TTS unificado — usa el engine correcto segun el dispositivo."""
        profile = self.get_profile()
        if profile.tts_engine == "text":
            return text  # modo ahorro, solo texto
        elif profile.tts_engine == "termux-tts" and self.is_pixel():
            # TTS nativo Android via Termux (safe subprocess, no os.system)
            import subprocess

            safe_text = text.replace("\n", " ")[:500]
            subprocess.run(
                ["termux-tts-speak", "-l", "es", safe_text], capture_output=True, timeout=10
            )
            return f"[TTS] {text[:50]}..."
        elif profile.tts_engine == "edge-tts":
            # edge-tts en PC (async, mejor calidad)
            try:
                import asyncio

                import edge_tts

                async def _speak():
                    communicate = edge_tts.Communicate(
                        text=text,
                        voice="es-ES-ElviraNeural",
                        rate="+8%",
                    )
                    await communicate.save("daniela_voice.mp3")
                    subprocess.run(
                        ["mpv", "--really-quiet", "daniela_voice.mp3"],
                        capture_output=True,
                        timeout=15,
                    )

                asyncio.run(_speak())
                return f"[TTS] {text[:50]}..."
            except ImportError:
                return f"[TTS fallback] {text}"
        return text

    def listen(self, timeout: int = 5) -> str | None:
        """STT unificado — escucha en el dispositivo correcto."""
        profile = self.get_profile()
        if profile.stt_engine == "disabled":
            return None
        elif profile.stt_engine == "termux-stt" and self.is_pixel():
            import subprocess

            try:
                result = subprocess.run(
                    ["termux-speech-to-text"], capture_output=True, text=True, timeout=timeout
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().lower()
            except Exception:
                return None
        elif profile.stt_engine == "whisper":
            # Whisper local en PC (gratis, mejor calidad)
            try:
                # Primero grabar audio
                import subprocess

                subprocess.run(
                    [
                        "python",
                        "-c",
                        "import sounddevice, scipy.io.wavfile as w; "
                        "import numpy as np; data = sounddevice.rec(int(44100*5), 44100, 1, 'float32'); "
                        "sounddevice.wait(); w.write('input.wav', 44100, (data*32767).astype(np.int16))",
                    ],
                    timeout=timeout + 5,
                )
                # Transcribir con faster-whisper
                from faster_whisper import WhisperModel

                model = WhisperModel("tiny", device="cpu")
                segments, _ = model.transcribe("input.wav", language="es")
                return " ".join([s.text for s in segments]).strip().lower()
            except ImportError:
                # Fallback: input manual
                return input("Comandante > ").strip().lower() or None
        return None

    def sync_state(self) -> dict:
        """Sincroniza estado entre PC y Pixel. En el PC, llama al Pixel via bridge."""
        state = {
            "device": self._device or self.detect_device(),
            "battery_pct": self._battery_pct,
            "profile": asdict(self.get_profile()) if self._profile else {},
            "detected_at": self._detected_at,
            "timestamp": datetime.now().isoformat(),
        }

        if self.is_pc():
            # En el PC, pedir estado al Pixel via bridge
            try:
                from pixel_bridge_hub import pixel_bridge

                pixel_status = pixel_bridge.get_status()
                state["pixel_online"] = pixel_status.get("online", False)
                state["pixel_battery"] = pixel_status.get("battery", {})
                state["pixel_location"] = pixel_status.get("location", {})
                # Si el Pixel reporta bateria, actualizar nuestro profile
                bat = pixel_status.get("battery", {})
                if isinstance(bat, dict) and "percentage" in bat:
                    self.update_battery(bat["percentage"])
            except ImportError:
                pass

        self._save_state()
        return state

    def get_status(self) -> dict:
        """Estado del dual-mode switch."""
        return {
            "device": self._device or self.detect_device(),
            "is_pixel": self.is_pixel(),
            "is_pc": self.is_pc(),
            "battery_pct": self._battery_pct,
            "profile": asdict(self.get_profile()),
            "detected_at": self._detected_at,
            "state_file": str(STATE_FILE),
        }


# Singleton
dual_mode = DualModeSwitch()


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  DUAL-MODE AUTO-SWITCH (PA-06)")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("  Usage: python dual_mode_switch.py detect|status|speak|listen|sync")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "detect":
        device = dual_mode.detect_device()
        print(f"  Device: {device}")
        print(f"  Platform: {platform.platform()}")

    elif cmd == "status":
        status = dual_mode.get_status()
        print(f"  Device: {status['device']}")
        print(f"  Is Pixel: {status['is_pixel']}")
        print(f"  Is PC: {status['is_pc']}")
        print(f"  Battery: {status['battery_pct']}%")
        print(f"  Profile: {json.dumps(status['profile'], indent=2)}")

    elif cmd == "speak":
        text = " ".join(sys.argv[2:]) or "Hola comandante, deteccion automatica activada."
        result = dual_mode.speak(text)
        print(f"  Result: {result}")

    elif cmd == "listen":
        print("  Listening...")
        result = dual_mode.listen(timeout=5)
        print(f"  Heard: {result}")

    elif cmd == "sync":
        state = dual_mode.sync_state()
        print(f"  {json.dumps(state, indent=2)}")

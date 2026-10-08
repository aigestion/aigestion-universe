"""Studio: Crea contenido viral automáticamente usando tools."""

import os
from pathlib import Path
from typing import Any

from tools.ai_tools import gemini_generate
from tools.content_tools import (
    create_video_from_images,
    generate_tts,
    transcribe_audio,
)

from ..base import Agent


class StudioAgent(Agent):
    """Agente que crea contenido viral para TikTok/Shorts."""

    def __init__(self, config: dict | None = None):
        super().__init__("studio", config)
        self.output_dir = Path(os.path.expanduser("~/videos/output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("/tmp/aig_studio")
        self.temp_dir.mkdir(exist_ok=True)

    def transcribe_video(self, video_path: str) -> str:
        """Transcribe un video usando Whisper."""
        result = transcribe_audio(video_path)
        return result.get("text", "")

    def generate_script(self, transcription: str) -> str:
        """Genera un guion viral desde la transcripción."""
        prompt = f"""Genera un guion viral para TikTok basado en este contenido.
        Debe tener: hook (primeros 3 segundos), 3 puntos clave, y CTA final.
        Máximo 60 segundos de video.

        Contenido:
        {transcription[:2000]}"""

        result = gemini_generate(prompt)
        return (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

    def generate_voice(self, script: str, output_path: str) -> bool:
        """Genera voz con Piper."""
        result = generate_tts(script, output_path)
        return result.get("success", False)

    def create_video(self, audio_path: str, images: list[str], output_path: str) -> bool:
        """Crea video con FFmpeg."""
        result = create_video_from_images(images, audio_path, output_path)
        return result.get("success", False)

    def run(self) -> dict[str, Any]:
        """Ejecuta el ciclo de creación."""
        self.start()
        try:
            # Buscar videos pendientes de procesar
            videos_dir = Path(os.path.expanduser("~/videos/interesting"))
            pending = list(videos_dir.glob("*.mp4"))[:3]

            created = []
            for video_path in pending:
                self.log(f"Procesando: {video_path.name}")
                transcription = self.transcribe_video(str(video_path))
                if transcription:
                    script = self.generate_script(transcription)
                    audio_path = str(self.temp_dir / f"{video_path.stem}_voice.wav")
                    if self.generate_voice(script, audio_path):
                        output_path = str(self.output_dir / f"viral_{video_path.stem}.mp4")
                        if self.create_video(audio_path, [], output_path):
                            created.append(output_path)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(created)} videos creados"
            self.save_metrics()
            self.log(f"Videos creados: {len(created)}")
            return {"created": created}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()

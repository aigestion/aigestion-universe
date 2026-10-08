"""Pipeline de Contenido Automatizado.

Scout → Studio → Social completamente automatizado.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.ai_tools import gemini_generate
from tools.content_tools import (
    create_video_from_images,
    generate_tts,
    transcribe_audio,
)
from tools.social_tools import post_to_instagram, post_to_tiktok, post_to_twitter

from .base import Agent


class ContentPipeline(Agent):
    """Pipeline de contenido automatizado."""

    def __init__(self, config: dict | None = None):
        super().__init__("content_pipeline", config)
        self.output_dir = Path(os.path.expanduser("~/videos/output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_video(self, video_path: str) -> dict[str, Any]:
        """Procesa un video completo."""
        # 1. Transcribir
        transcription = transcribe_audio(video_path)

        # 2. Generar guion
        prompt = f"Genera un guion viral: {transcription.get('text', '')[:1000]}"
        script_result = gemini_generate(prompt)
        script = (
            script_result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        # 3. Generar voz
        audio_path = str(self.output_dir / f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
        voice_result = generate_tts(script, audio_path)

        # 4. Crear video
        output_path = str(self.output_dir / f"viral_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        video_result = create_video_from_images([], audio_path, output_path)

        return {
            "transcription": transcription,
            "script": script,
            "voice": voice_result,
            "video": video_result,
        }

    def publish(self, video_path: str, description: str) -> dict[str, Any]:
        """Publica en todas las redes."""
        results = {}
        results["tiktok"] = post_to_tiktok(video_path, description)
        results["twitter"] = post_to_twitter(description)
        results["instagram"] = post_to_instagram(video_path, description)
        return results

    def run(self) -> dict[str, Any]:
        """Ejecuta el pipeline completo."""
        self.start()
        try:
            # Buscar videos pendientes
            videos_dir = Path(os.path.expanduser("~/videos/interesting"))
            pending = list(videos_dir.glob("*.mp4"))[:3]

            results = []
            for video_path in pending:
                result = self.process_video(str(video_path))
                results.append(result)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(results)} videos procesados"
            self.save_metrics()
            return {"results": results}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()

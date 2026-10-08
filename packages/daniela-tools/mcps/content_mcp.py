"""MCP para tools de contenido."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.content_tools import (
    create_video_from_images,
    download_video,
    generate_tts,
    get_video_info,
    transcribe_audio,
)


class ContentMCP:
    """MCP para creación de contenido."""

    def __init__(self):
        self.tools = {
            "create_video": self.create_video,
            "transcribe": self.transcribe,
            "generate_tts": self.generate_tts,
            "download_video": self.download_video,
            "get_video_info": self.get_video_info,
        }

    def create_video(self, images: list[str], audio: str, output: str) -> dict[str, Any]:
        """Crea un video."""
        return create_video_from_images(images, audio, output)

    def transcribe(self, audio_path: str, model: str = "base") -> dict[str, Any]:
        """Transcribe audio."""
        return transcribe_audio(audio_path, model)

    def generate_tts(self, text: str, output: str, voice: str = "en_US-lessac-medium") -> dict[str, Any]:
        """Genera voz."""
        return generate_tts(text, output, voice)

    def download_video(self, url: str, output_dir: str = "~/videos") -> dict[str, Any]:
        """Descarga un video."""
        return download_video(url, output_dir)

    def get_video_info(self, url: str) -> dict[str, Any]:
        """Obtiene info de un video."""
        return get_video_info(url)

    def call(self, tool: str, **kwargs) -> Any:
        """Llama a un tool."""
        if tool in self.tools:
            return self.tools[tool](**kwargs)
        return {"error": f"Tool '{tool}' no encontrado"}

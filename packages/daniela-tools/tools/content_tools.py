"""Tools para creación y gestión de contenido."""

import json
import subprocess
from pathlib import Path
from typing import Any


def create_video_from_images(images: list[str], audio: str, output: str) -> dict[str, Any]:
    """Crea un video desde imágenes y audio."""
    try:
        # Crear lista de imágenes para FFmpeg
        list_file = Path("/tmp/aig_ffmpeg_list.txt")
        with open(list_file, "w") as f:
            for img in images:
                f.write(f"file '{img}'\n")
                f.write("duration 3\n")

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-i", audio,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {"success": result.returncode == 0, "output": output}
    except Exception as e:
        return {"error": str(e)}


def transcribe_audio(audio_path: str, model: str = "base") -> dict[str, Any]:
    """Transcribe audio con Whisper."""
    try:
        cmd = [
            "whisper",
            audio_path,
            "--model", model,
            "--output_dir", "/tmp/aig_transcribe",
            "--output_format", "txt",
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        txt_file = Path("/tmp/aig_transcribe") / f"{Path(audio_path).stem}.txt"
        if txt_file.exists():
            return {"text": txt_file.read_text(), "status": "ok"}
        return {"error": "Transcripción fallida"}
    except Exception as e:
        return {"error": str(e)}


def generate_tts(text: str, output: str, voice: str = "en_US-lessac-medium") -> dict[str, Any]:
    """Genera voz con Piper."""
    try:
        cmd = [
            "piper",
            "--model", voice,
            "--output_file", output,
        ]
        result = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=120)
        return {"success": result.returncode == 0, "output": output}
    except Exception as e:
        return {"error": str(e)}


def download_video(url: str, output_dir: str = "~/videos") -> dict[str, Any]:
    """Descarga un video con yt-dlp."""
    try:
        output_path = Path(output_dir).expanduser() / "%(title)s.%(ext)s"
        cmd = [
            "yt-dlp",
            "-f", "best[height<=720]",
            "-o", str(output_path),
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {"success": result.returncode == 0, "output": result.stdout}
    except Exception as e:
        return {"error": str(e)}


def get_video_info(url: str) -> dict[str, Any]:
    """Obtiene información de un video."""
    try:
        cmd = ["yt-dlp", "--dump-json", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": "No se pudo obtener info"}
    except Exception as e:
        return {"error": str(e)}

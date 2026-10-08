import json
import os
import subprocess

MEDIA_DIR = os.path.expanduser("~/daniela-os/media")
RESEARCH_DIR = os.path.expanduser("~/daniela-os/research")
os.makedirs(MEDIA_DIR, exist_ok=True)

# 1. Cargar el Storyboard
with open(os.path.join(RESEARCH_DIR, "storyboard_studio.json"), encoding="utf-8") as f:
    storyboard = json.load(f)

texto_completo = " ".join([e["audio"] for e in storyboard])
audio_path = os.path.join(MEDIA_DIR, "storyboard_audio.mp3")
video_path = os.path.join(MEDIA_DIR, "storyboard_final.mp4")

print("🎙️ [DANIELA OS]: Sintetizando locución de las 3 escenas...")
subprocess.run(
    [
        "edge-tts",
        "--voice",
        "es-ES-ElviraNeural",
        "--text",
        texto_completo,
        "--write-media",
        audio_path,
    ]
)

print("🎬 [DANIELA OS]: Compilando vídeo del Storyboard (1080x1920)...")
filter_complex = "[0:a]showwaves=s=1080x400:mode=line:colors=0x00f0ff[vwave];color=c=0x0b0f19:s=1080x1920[bg];[bg][vwave]overlay=(W-w)/2:(H-h)/2[v]"
cmd_video = [
    "ffmpeg",
    "-y",
    "-i",
    audio_path,
    "-filter_complex",
    filter_complex,
    "-map",
    "[v]",
    "-map",
    "0:a",
    "-c:v",
    "libx264",
    "-c:a",
    "aac",
    "-shortest",
    video_path,
]
subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Levantar servidor web local
subprocess.run(["pkill", "-f", "http.server"])
subprocess.Popen(
    ["python3", "-m", "http.server", "8080", "--directory", MEDIA_DIR],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

print("\n✨ [ÉXITO TOTAL]: Vídeo del Storyboard generado con éxito.")
print(f"📹 Archivo: {video_path}")
print("🌐 Disponible en: http://localhost:8080/storyboard_final.mp4")

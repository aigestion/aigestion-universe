import os
import subprocess

MEDIA_DIR = os.path.expanduser("~/daniela-os/media")
input_audio = os.path.join(MEDIA_DIR, "vids_master_audio.mp3")
output_video_termux = os.path.join(MEDIA_DIR, "vids_universal.mp4")
output_video_public = "/sdcard/Download/vids_universal.mp4"

print(
    "🛠️ [DANIELA OS]: Re-codificando vídeo con máxima compatibilidad universal (30 FPS, YUV420p)..."
)

# Renderizado FFmpeg ultra-compatible
filter_complex = "[0:a]showwaves=s=1080x400:mode=line:colors=0x00ffff|0xff00ff[vwave];color=c=0x0b0f19:s=1080x1920[bg];[bg][vwave]overlay=(W-w)/2:(H-h)/2[v]"

cmd_ffmpeg = [
    "ffmpeg",
    "-y",
    "-i",
    input_audio,
    "-filter_complex",
    filter_complex,
    "-map",
    "[v]",
    "-map",
    "0:a",
    "-c:v",
    "libx264",
    "-profile:v",
    "baseline",
    "-level",
    "3.0",
    "-pix_fmt",
    "yuv420p",
    "-r",
    "30",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-ar",
    "44100",
    "-ac",
    "2",
    "-shortest",
    output_video_termux,
]

subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Copiar a Descargas
subprocess.run(["cp", output_video_termux, output_video_public], check=False)

# Crear reproductor HTML5 local para Chrome
html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniela OS - Visualizador Táctico</title>
    <style>
        body { background-color: #0b0f19; color: #00ffff; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        h2 { margin-bottom: 20px; text-shadow: 0 0 10px #00ffff; }
        video { width: 90%; max-width: 400px; border: 2px solid #ff00ff; border-radius: 12px; box-shadow: 0 0 20px rgba(255,0,255,0.4); }
    </style>
</head>
<body>
    <h2>🎬 Daniela OS - Vids Master</h2>
    <video controls autoplay loop playsinline src="/vids_universal.mp4"></video>
</body>
</html>
"""

with open(os.path.join(MEDIA_DIR, "player.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

# Reiniciar servidor web en el puerto 8080
subprocess.run(["pkill", "-f", "http.server"], check=False)
subprocess.Popen(
    ["python3", "-m", "http.server", "8080", "--directory", MEDIA_DIR],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

print("\n✨ [REPARACIÓN COMPLETADA]:")
print("🌐 Opción 1 (Chrome): Abre http://localhost:8080/player.html")
print("📁 Opción 2 (Archivos del móvil): Descargas / vids_universal.mp4")

import os
import subprocess

MEDIA_DIR = os.path.expanduser("~/daniela-os/media")
audio_file = os.path.join(MEDIA_DIR, "vids_master_audio.mp3")
output_termux = os.path.join(MEDIA_DIR, "vids_master_real.mp4")
output_public = "/sdcard/Download/vids_master_real.mp4"

print("🎬 [DANIELA OS]: Renderizando motor gráfico de vídeo dinámico...")

# Filtro avanzado: Espectro de barras cian/magenta + Texto en pantalla + Fondo animado
filter_graph = (
    "color=c=0x0a0e17:s=1080x1920:d=16[bg];"
    "[0:a]showfreqs=s=900x500:mode=bar:colors=0x00ffff|0xff00ff:ascale=log[freq];"
    "[bg][freq]overlay=(W-w)/2:(H-h)/2+100[v1];"
    "[v1]drawtext=text='DANIELA OS - AIGESTION.NET':fontcolor=0x00ffff:fontsize=48:x=(w-text_w)/2:y=200,"
    "drawtext=text='[ CIBER-EJECUTIVO SOVERANO ]':fontcolor=0xff00ff:fontsize=32:x=(w-text_w)/2:y=270,"
    "drawtext=text='PROCESANDO FLUJOS TACTICOS...':fontcolor=0xffffff:fontsize=28:x=(w-text_w)/2:y=1500[v]"
)

cmd_ffmpeg = [
    "ffmpeg",
    "-y",
    "-i",
    audio_file,
    "-filter_complex",
    filter_graph,
    "-map",
    "[v]",
    "-map",
    "0:a",
    "-c:v",
    "libx264",
    "-preset",
    "ultrafast",
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
    "-shortest",
    output_termux,
]

subprocess.run(cmd_ffmpeg)

# Copiar a Descargas de Android
subprocess.run(["cp", output_termux, output_public], check=False)

# Actualizar el HTML del reproductor
html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniela OS - Vids Real</title>
    <style>
        body { background-color: #0b0f19; color: #00ffff; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        video { width: 90%; max-width: 400px; border: 2px solid #00ffff; border-radius: 12px; box-shadow: 0 0 25px rgba(0,255,255,0.5); }
    </style>
</head>
<body>
    <h2>🎬 Daniela OS - Vídeo Dinámico Real</h2>
    <video controls autoplay loop playsinline src="/vids_master_real.mp4"></video>
</body>
</html>
"""

with open(os.path.join(MEDIA_DIR, "player.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print(
    "\n✨ [RENDERIZADO COMPLETADO] El vídeo ahora cuenta con espectro gráfico de frecuencia y títulos."
)

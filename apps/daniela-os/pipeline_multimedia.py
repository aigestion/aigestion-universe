import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

print("🎙️ [DANIELA OS]: Generando síntesis de voz neural...")
texto = "Daniela OS opera a máxima capacidad. Todos los sistemas multimodal y de red están sincronizados."
audio_out = os.path.join(MEDIA_DIR, "vids_master_audio.mp3")

# Sintetizar audio con Edge-TTS
subprocess.run(
    ["edge-tts", "--voice", "es-ES-ElviraNeural", "--text", texto, "--write-media", audio_out]
)

print("🎬 [DANIELA OS]: Renderizando vídeo con espectro dinámico...")
video_out = os.path.join(MEDIA_DIR, "vids_master_render.mp4")
filter_graph = (
    "color=c=0x0a0e17:s=1080x1920:d=10[bg];"
    "[0:a]showfreqs=s=900x500:mode=bar:colors=0x00ffff|0xff00ff:ascale=log[freq];"
    "[bg][freq]overlay=(W-w)/2:(H-h)/2+100[v1];"
    "[v1]drawtext=text='DANIELA OS - AIGESTION.NET':fontcolor=0x00ffff:fontsize=48:x=(w-text_w)/2:y=200,"
    "drawtext=text='[ SISTEMA OPERATIVO ACTIVO ]':fontcolor=0xff00ff:fontsize=32:x=(w-text_w)/2:y=270[v]"
)

cmd = [
    "ffmpeg",
    "-y",
    "-i",
    audio_out,
    "-filter_complex",
    filter_graph,
    "-map",
    "[v]",
    "-map",
    "0:a",
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-shortest",
    video_out,
]
subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("🟢 Pipeline finalizado con éxito.")

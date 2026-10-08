import os
import subprocess

MEDIA_DIR = os.path.expanduser("~/daniela-os/media")
os.makedirs(MEDIA_DIR, exist_ok=True)

AUDIO_FILE = os.path.join(MEDIA_DIR, "notebooklm_summary.mp3")
VIDEO_FILE = os.path.join(MEDIA_DIR, "notebooklm_presentation.mp4")

# 1. Guion Extendido de AIGestion.net
GUION_EXTENDIDO = (
    "Informe de arquitectura estratégica Daniela OS para AIGestion.net. "
    "En un mercado dominado por la sobrecarga burocrática y el riesgo de privacidad, "
    "desplegamos una solución de Inteligencia Artificial Soberana. "
    "Nuestra infraestructura integra tres capas fundamentales: "
    "Capa Vocal con atención veinticuatro siete y latencia ultrabaja; "
    "Capa de Integración con Google Workspace, Telegram y Bóveda Cifrada en Drive; "
    "y Capa de Gobernanza con la filosofía Human-in-the-Loop, donde cada acción crítica requiere tu aprobación. "
    "Con un techo de gasto garantizado a nivel de código local y privacidad absoluta, "
    "AIGestion.net convierte tu negocio en una estación de operaciones eficiente. "
    "Tu negocio, tu vida, en orden absoluto."
)

print("🎙️ [DANIELA OS]: Generando locución extendida...")
cmd_audio = [
    "edge-tts",
    "--voice",
    "es-ES-ElviraNeural",
    "--text",
    GUION_EXTENDIDO,
    "--write-media",
    AUDIO_FILE,
]
subprocess.run(cmd_audio)

print("🎬 [DANIELA OS]: Compilando vídeo táctico dinámico (Onda + Texto)...")
# Genera un vídeo vertical 1080x1920 con visualizador de ondas y texto estático de marca
filter_complex = (
    "[0:a]showwaves=s=1080x400:mode=line:colors=0x00f0ff[vwave];"
    "color=c=0x0b0f19:s=1080x1920[bg];"
    "[bg][vwave]overlay=(W-w)/2:(H-h)/2[v]"
)

cmd_video = [
    "ffmpeg",
    "-y",
    "-i",
    AUDIO_FILE,
    "-filter_complex",
    filter_complex,
    "-map",
    "[v]",
    "-map",
    "0:a",
    "-c:v",
    "libx264",
    "-preset",
    "fast",
    "-crf",
    "23",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-pix_fmt",
    "yuv420p",
    "-shortest",
    VIDEO_FILE,
]

subprocess.run(cmd_video)

# Renovar servidor web local
subprocess.run(["pkill", "-f", "http.server"])
subprocess.Popen(
    ["python3", "-m", "http.server", "8080", "--directory", MEDIA_DIR],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

print("\n✅ [PROCESO COMPLETADO]: Accede a http://localhost:8080 en tu navegador.")

import json
import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os")
RESEARCH_DIR = os.path.join(BASE_DIR, "research")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

print("🎬 [DANIELA OS]: Inicializando Pipeline de Producción para Google Vids...")

# 1. Crear el Guion Táctico sincronizado (Estructura de 4 bloques de 16s)
vids_script = [
    {
        "bloque": 1,
        "escena_A": "Caos burocrático, carpetas rojas y notificaciones pendientes.",
        "escena_B": "Ampliación del riesgo y pérdida de tiempo operativo.",
        "locucion": "El caos administrativo drena tus recursos y destruye tu margen operativo. Es hora de tomar el control total.",
    },
    {
        "bloque": 2,
        "escena_A": "Aparición de Daniela OS con interfaz cian y neón magenta.",
        "escena_B": "Procesamiento ultrarrápido de documentos en pantalla.",
        "locucion": "Daniela OS automatiza tus flujos de trabajo en segundos con soberanía absoluta y arquitectura local.",
    },
    {
        "bloque": 3,
        "escena_A": "Panel de control con métricas de rendimiento y costes en verde.",
        "escena_B": "Sincronización segura de archivos en la Bóveda de Google Drive.",
        "locucion": "Garantiza el cumplimiento burocrático, reduce tus costes a cero y mantén siempre el control humano.",
    },
    {
        "bloque": 4,
        "escena_A": "Interfaz ciber-ejecutiva de Google Workspace y AI Studio.",
        "escena_B": "Cierre con logotipo oficial y llamada a la acción.",
        "locucion": "Visita AIGestion.net y transforma tus operaciones hoy mismo. Tu negocio, tu vida, en orden absoluto.",
    },
]

# Save JSON for Google Vids / Veed import
json_output = os.path.join(RESEARCH_DIR, "google_vids_project.json")
with open(json_output, "w", encoding="utf-8") as f:
    json.dump(vids_script, f, indent=2, ensure_ascii=False)

print(f"📄 Guion técnico exportado para Vids en: {json_output}")

# 2. Generar el Audio Unificado de Locución (Neural Voice)
texto_completo = " ".join([b["locucion"] for b in vids_script])
audio_output = os.path.join(MEDIA_DIR, "vids_master_audio.mp3")

print("🎙️ Sintetizando voz en off continuada para Vids...")
subprocess.run(
    [
        "edge-tts",
        "--voice",
        "es-ES-ElviraNeural",
        "--text",
        texto_completo,
        "--write-media",
        audio_output,
    ]
)

# 3. Compilar el Vídeo Master H.264
video_output = os.path.join(MEDIA_DIR, "vids_master_render.mp4")
print("⚡ Renderizando vídeo sincronizado en formato vertical 9:16 (1080x1920)...")

filter_complex = "[0:a]showwaves=s=1080x400:mode=line:colors=0x00ffff|0xff00ff[vwave];color=c=0x0b0f19:s=1080x1920[bg];[bg][vwave]overlay=(W-w)/2:(H-h)/2[v]"
cmd_ffmpeg = [
    "ffmpeg",
    "-y",
    "-i",
    audio_output,
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
    "-c:a",
    "aac",
    "-ar",
    "44100",
    "-ac",
    "2",
    "-shortest",
    video_output,
]
subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 4. Copiar a la carpeta pública de Descargas para visualizar en el móvil
public_output = "/sdcard/Download/vids_master_daniela.mp4"
subprocess.run(["cp", video_output, public_output], check=False)

print("\n✨ [PIPELINE DE VÍDEO COMPLETADO]:")
print(f"📹 MP4 Renderizado : {video_output}")
print(f"📱 Copia en Móvil : {public_output}")
print(f"📋 Proyecto Vids  : {json_output}")

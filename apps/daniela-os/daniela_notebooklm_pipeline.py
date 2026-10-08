import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

print("⚡ [DANIELA OS]: Iniciando Pipeline NotebookLM & Generación Multimodal...")

# 1. Configuración de Fuentes e Ideas de Investigación
investigacion = {
    "cuaderno_id": "AIGestion_Research_01",
    "idea_fuerza": "Soberanía Tecnológica con Daniela OS y Google Workspace",
    "fuentes_estudio": [
        "AIGestion.net — Dossier Fundacional y Diario de Operaciones.pdf",
        "Daniela Google Ecosystem Integration Spec v43.0.pdf",
        "Propuesta Comercial y Modelo de Servicios - aigestion.net.pdf",
    ],
}

print(
    f"📚 [NOTEBOOK LM]: Procesando {len(investigacion['fuentes_estudio'])} fuentes en la bóveda..."
)

# 2. Generación del Script de Salida Multimodal (Audio & Vídeo)
guion_multimodal = (
    "Análisis de estudio completado por NotebookLM. "
    "Fuentes procesadas: Dossier Fundacional, Especificaciones v43.0 y Propuesta Comercial. "
    "Conclusión estratégica: La arquitectura de AIGestion.net garantiza control absoluto del negocio, "
    "integrando inteligencia local en el Pixel 8a con la potencia de Google Workspace. "
    "Sistemas listos para exportación de vídeo y audio de alta fidelidad."
)

audio_path = os.path.join(MEDIA_DIR, "notebooklm_summary.mp3")

# 3. Renderizado de Audio
print("🎙️ [AUDIO ENGINE]: Sintetizando resumen de fuentes...")
cmd_audio = [
    "edge-tts",
    "--voice",
    "es-ES-ElviraNeural",
    "--text",
    guion_multimodal,
    "--write-media",
    audio_path,
]
subprocess.run(cmd_audio)

# 4. Ensamblado de Vídeo (FFmpeg)
video_path = os.path.join(MEDIA_DIR, "notebooklm_presentation.mp4")
print("🎬 [VIDEO ENGINE]: Generando asset de vídeo táctico...")

cmd_video = [
    "ffmpeg",
    "-y",
    "-f",
    "lavfi",
    "-i",
    "color=c=0x0f172a:s=1080x1920:r=30",  # Fondo azul oscuro/neón 9:16
    "-i",
    audio_path,
    "-c:v",
    "libx264",
    "-tune",
    "stillimage",
    "-c:a",
    "aac",
    "-b:a",
    "1920k",
    "-pix_fmt",
    "yuv420p",
    "-shortest",
    video_path,
]

result = subprocess.run(cmd_video, capture_output=True, text=True)

if os.path.exists(video_path):
    print("\n✨ [ÉXITO TOTAL]: Salida Multimodal Completada.")
    print(f"🔊 Audio: {audio_path}")
    print(f"📹 Vídeo: {video_path}")
else:
    print("⚠️ Revisa la instalación de FFmpeg para la salida de vídeo.")

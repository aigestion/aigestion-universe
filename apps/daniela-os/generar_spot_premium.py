import os
import subprocess

SPOT_DIR = os.path.expanduser("~/daniela-os/media")
os.makedirs(SPOT_DIR, exist_ok=True)

AUDIO_FILE = os.path.join(SPOT_DIR, "spot_master_premium.mp3")

GUION_LOCUCION = (
    "En un mundo dominado por la nube pública y la burocracia desbordada, "
    "el tiempo es el único activo que jamás se recupera. "
    "La verdadera soberanía tecnológica no se alquila: se ejecuta en tu propio bolsillo. "
    "Daniela OS. Inteligencia autónoma, ciberdefensa en tiempo real y bóveda cifrada local. "
    "AIGestion.net. Tu negocio, tu vida, en orden absoluto."
)

print("🎙️ [DANIELA OS]: Generando locución neuronal para el Spot Máster Premium...")

cmd = [
    "edge-tts",
    "--voice",
    "es-ES-ElviraNeural",
    "--text",
    GUION_LOCUCION,
    "--write-media",
    AUDIO_FILE,
]

subprocess.run(cmd)

print(f"✅ [SPOT RENDERIZADO]: {AUDIO_FILE}")
print("📺 Puedes reproducir el audio directamente o visualizarlo en el panel táctico local.")

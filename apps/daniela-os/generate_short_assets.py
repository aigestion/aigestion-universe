import os

from gtts import gTTS
from safe_exec import run_code

BASE_DIR = os.path.expanduser("~/daniela-os")

# 1. Texto oficial de Daniela para el Short
DAN_TEXT = "Facturas clasificadas en Google Drive, borradores redactados en Gmail y informe listo, Comandante."

# 2. Sintetizar la pista de Daniela
print("🎙️ [AUTOMATION]: Generando voz sintética de Daniela...")
tts = gTTS(text=DAN_TEXT, lang="es", tld="es")
voice_path = os.path.join(BASE_DIR, "tmp_voice_daniela.mp3")
tts.save(voice_path)

# 3. Vincular imagen oficial de Daniela para la animación
img_src = "/storage/emulated/0/DCIM/Restored/ChatGPT Image 22 abr 2026, 22_22_52.png"
img_dst = os.path.join(BASE_DIR, "environment_base.jpg")

if os.path.exists(img_src):
    run_code(f'cp "{img_src}" "{img_dst}"')
    print("📸 [AUTOMATION]: Rostro oficial de Daniela vinculado a la pipeline.")

print("\n✨ [ÉXITO PREMIUM]: Pistas de audio y activos listos para el renderizador.")

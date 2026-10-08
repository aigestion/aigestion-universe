import os

MEDIA_DIR = os.path.expanduser("~/daniela-os/media")
ARCHIVOS_A_MANTENER = ["storyboard_android.mp4", "index.html", "spot_master_premium.mp3"]

print("🧹 [DANIELA OS]: Iniciando limpieza de activos obsoletos...")

for archivo in os.listdir(MEDIA_DIR):
    if archivo not in ARCHIVOS_A_MANTENER:
        ruta_completa = os.path.join(MEDIA_DIR, archivo)
        os.remove(ruta_completa)
        print(f"🗑️ Eliminado: {archivo}")

print("✨ [BÓVEDA]: Mantenimiento completado. Espacio optimizado.")

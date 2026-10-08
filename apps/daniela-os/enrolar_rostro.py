import os
import time

from safe_exec import run_cmd

PROFILE_DIR = os.path.expanduser("~/daniela-os/biometric_profile")


def tomar_captura_facial(nombre_archivo):
    print(f"📸 Capturando {nombre_archivo}...")
    filepath = os.path.join(PROFILE_DIR, nombre_archivo)
    # Cámara frontal id=1 en la mayoría de terminales Android
    run_cmd(["termux-camera-photo", "-c", "1", filepath])
    time.sleep(1.5)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        print(f"✅ Imagen guardada correctamente: {filepath}")
        return True
    else:
        print(f"⚠️ Error al capturar {nombre_archivo}. Verifique permisos de cámara.")
        return False


print("=== 👁️ ENROLAMIENTO BIOMÉTRICO FACIAL DE ALEJANDRO ===")
print("Mira fijamente a la cámara frontal de tu Pixel...")
time.sleep(2)

# Secuencia de 3 tomas para mayor precisión
exitos = 0
for i in range(1, 4):
    print(f"\n[Toma {i}/3] Prepárate...")
    time.sleep(1)
    if tomar_captura_facial(f"alejandro_face_{i}.jpg"):
        exitos += 1

if exitos > 0:
    print("\n🎉 ¡Mapeo facial completado con éxito!")
    print(f"Se han registrado {exitos} imágenes patrón en {PROFILE_DIR}")
else:
    print(
        "\n❌ No se pudo completar el enrolamiento. Asegúrate de otorgar permisos de cámara a Termux API."
    )

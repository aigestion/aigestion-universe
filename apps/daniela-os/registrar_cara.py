import os
import time

import numpy as np
from PIL import Image
from safe_exec import run_code

ruta_foto = os.path.expanduser("~/daniela-os/foto_referencia.jpg")
ruta_matriz = os.path.expanduser("~/daniela-os/rostro_referencia.npy")

# Limpiar capturas previas si existen
if os.path.exists(ruta_foto):
    os.remove(ruta_foto)

print("📸 Colócate frente a la cámara. Capturando foto en 2 segundos...")
time.sleep(2)

# Intentar captura (Cámara frontal -c 1 o trasera -c 0 como respaldo)
run_code(f"termux-camera-photo -c 1 {ruta_foto}")

# Dar tiempo a Termux/Android para volcar el archivo a disco
timeout = 5
while timeout > 0 and (not os.path.exists(ruta_foto) or os.path.getsize(ruta_foto) == 0):
    time.sleep(0.5)
    timeout -= 0.5

# Si falla con la cámara 1, intentar con la 0
if not os.path.exists(ruta_foto) or os.path.getsize(ruta_foto) == 0:
    print("⚠️ Reintentando captura con cámara secundaria...")
    run_code(f"termux-camera-photo -c 0 {ruta_foto}")
    time.sleep(2)

# Procesar la imagen si es válida
if os.path.exists(ruta_foto) and os.path.getsize(ruta_foto) > 0:
    try:
        img = Image.open(ruta_foto).convert("L").resize((100, 100))
        matriz = np.array(img, dtype=np.float32)
        np.save(ruta_matriz, matriz)
        print("✅ ¡Rostro de Alejandro registrado y guardado en 'rostro_referencia.npy'!")
    except Exception as e:
        print(f"❌ Error al procesar la imagen: {e}")
else:
    print("❌ Error: No se pudo obtener la captura. Revisa los permisos de cámara en Android.")

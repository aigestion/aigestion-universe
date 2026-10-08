import json
import os

import numpy as np
from PIL import Image
from safe_exec import run_code

BD_ALIADOS = os.path.expanduser("~/daniela-os/aliados.json")
DIR_ROSTROS = os.path.expanduser("~/daniela-os/rostros")


def inicializar_entorno():
    os.makedirs(DIR_ROSTROS, exist_ok=True)
    if not os.path.exists(BD_ALIADOS):
        with open(BD_ALIADOS, "w") as f:
            json.dump({}, f)


def guardar_aliado(nombre, rol, matriz_cara):
    inicializar_entorno()

    # Cargar base existente
    with open(BD_ALIADOS) as f:
        data = json.load(f)

    # Guardar matriz .npy en carpeta dedicada
    ruta_npy = os.path.join(DIR_ROSTROS, f"{nombre.lower()}.npy")
    np.save(ruta_npy, matriz_cara)

    # Registrar metadata en JSON
    data[nombre] = {"rol": rol, "matriz": ruta_npy}

    with open(BD_ALIADOS, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Aliado {nombre} [{rol}] registrado exitosamente en Daniela OS.")


def capturar_y_registrar(nombre, rol="Aliado"):
    ruta_temp = os.path.expanduser("~/daniela-os/captura_temp.jpg")
    print(f"📸 Capturando rostro para {nombre}...")

    run_code(f"termux-camera-photo -c 1 {ruta_temp}")

    if os.path.exists(ruta_temp) and os.path.getsize(ruta_temp) > 0:
        try:
            img = Image.open(ruta_temp).convert("L").resize((100, 100))
            matriz = np.array(img, dtype=np.float32)
            guardar_aliado(nombre, rol, matriz)
            os.remove(ruta_temp)
        except Exception as e:
            print(f"❌ Error al procesar imagen: {e}")
    else:
        print("❌ Error al capturar imagen desde la cámara.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        nom = sys.argv[1]
        r = sys.argv[2] if len(sys.argv) > 2 else "Aliado"
        capturar_y_registrar(nom, r)
    else:
        print("Uso: python gestor_aliados.py <Nombre> <Rol>")

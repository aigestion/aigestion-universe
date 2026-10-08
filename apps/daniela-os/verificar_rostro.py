import os

import numpy as np
from PIL import Image
from safe_exec import run_cmd


def verificar_usuario():
    # 1. Capturar cara actual
    destino = os.path.expanduser("~/daniela-os/captura_actual.jpg")
    run_cmd(["termux-camera-photo", "-c", "0", destino])
    if not os.path.exists("captura_actual.jpg") and not os.path.exists(destino):
        return -1

    # 2. Procesar imagen
    try:
        img = Image.open("captura_actual.jpg").convert("L").resize((100, 100))
        matriz_actual = np.array(img, dtype=np.float32)

        # 3. Comparar con Alejandro
        ref_path = "rostro_referencia.npy"
        if not os.path.exists(ref_path):
            return -1

        matriz_ref = np.load(ref_path)

        # Calcular error cuadrático medio (MSE)
        mse = np.mean((matriz_actual - matriz_ref) ** 2)

        # Umbral (ajusta esto si detecta falsos negativos): 1000 es estricto
        if mse < 1500:
            return 0  # Es Alejandro
        else:
            return 1  # Es alguien más
    except Exception:
        return -1  # Error

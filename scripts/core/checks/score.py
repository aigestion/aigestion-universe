import os
import time

import numpy as np
from PIL import Image
from safe_exec import run_cmd

PROFILE_DIR = os.path.expanduser("~/daniela-os/biometric_profile")
CURRENT_PHOTO = os.path.expanduser("~/daniela-os/temp_check.jpg")

print("📸 Mira a la cámara frontal...")
run_cmd(["termux-camera-photo", "-c", "1", CURRENT_PHOTO])
time.sleep(1.2)

if os.path.exists(CURRENT_PHOTO):
    img_actual = Image.open(CURRENT_PHOTO).convert('L').resize((200, 200))
    arr_actual = np.array(img_actual, dtype=np.float32)

    for i in range(1, 4):
        patron_path = os.path.join(PROFILE_DIR, f"alejandro_face_{i}.jpg")
        if os.path.exists(patron_path):
            img_patron = Image.open(patron_path).convert('L').resize((200, 200))
            arr_patron = np.array(img_patron, dtype=np.float32)
            diff = np.mean(np.abs(arr_actual - arr_patron))
            print(f"📊 Diferencia real con Foto {i}: {diff:.2f}")

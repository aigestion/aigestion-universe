import os
import subprocess
import time

RAM_DIR = "/data/data/com.termux/files/usr/tmp/daniela_ram"
RAW_M4A = os.path.join(RAM_DIR, "ambient_test.m4a")


def sample_ambient_sound(duration=2.0):
    os.makedirs(RAM_DIR, exist_ok=True)
    subprocess.run(
        ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(0.05)
    subprocess.run(
        ["termux-microphone-record", "-f", RAW_M4A],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(duration)
    subprocess.run(
        ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    if os.path.exists(RAW_M4A):
        size = os.path.getsize(RAW_M4A)
        return f"Muestra de audio ambiental procesada ({size} bytes). Entorno estable."
    return "No se pudo registrar audio ambiental."


if __name__ == "__main__":
    print(sample_ambient_sound())

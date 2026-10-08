import os
import sys

from safe_exec import run_bg, run_code

SONIDOS_DIR = os.path.expanduser("~/daniela-os/sonidos")


def reproducir(fichero):
    ruta = os.path.join(SONIDOS_DIR, fichero)
    if os.path.exists(ruta):
        run_bg(["mpv", "--no-video", "--volume=100", ruta])
    else:
        run_code("termux-vibrate -d 300")


if __name__ == "__main__":
    evento = sys.argv[1] if len(sys.argv) > 1 else "DEFAULT"

    if evento in ["LLAMADA_VIP", "MSJ_URGENTE", "SOS"]:
        reproducir("cyber_alarm.wav")
    else:
        run_code("termux-vibrate -d 150")

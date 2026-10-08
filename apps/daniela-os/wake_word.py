import os
import subprocess
import time

from safe_exec import run_bg, run_code


def esperar_palabra_clave():
    print("👂 [WAKE WORD] Escuchando activación por voz ('Daniela')...")
    while True:
        try:
            # Captura de voz rápida de 4 segundos
            raw = (
                subprocess.check_output(
                    ["termux-speech-to-text"], stderr=subprocess.DEVNULL, timeout=5
                )
                .decode("utf-8")
                .strip()
                .lower()
            )
            if "daniela" in raw or "oye daniela" in raw:
                print("⚡ ¡Palabra clave detectada!")
                run_bg(
                    [
                        "mpv",
                        "--no-video",
                        "--ao=opensles",
                        "--volume=100",
                        os.path.expanduser("~/daniela-os/sonidos/cyber_alarm.wav"),
                    ]
                )
                run_code("termux-tts-speak 'Escuchando Comandante'")
                return True
        except Exception:
            pass
        time.sleep(1)


if __name__ == "__main__":
    esperar_palabra_clave()

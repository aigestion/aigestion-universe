import subprocess
import time

from safe_exec import run_code


def centinela():
    print("🛡️ [CENTINELA] Escucha activa en segundo plano...")
    while True:
        try:
            # Captura ultra-rápida de 2 segundos para buscar la palabra clave
            raw = (
                subprocess.check_output(
                    ["termux-speech-to-text"], stderr=subprocess.DEVNULL, timeout=4
                )
                .decode("utf-8")
                .strip()
                .lower()
            )

            if "daniela" in raw:
                print("⚡ ¡WAKE WORD DETECTADA!")
                # Ejecuta la lógica de conversación
                run_code("python ~/daniela-os/conversar_daniela.py")

        except Exception:
            # Silenciar errores de tiempo de espera o audio vacío
            pass

        # Intervalo de reposo para no agotar la batería
        time.sleep(2)


if __name__ == "__main__":
    centinela()

import os
import subprocess

from safe_exec import run_bg, run_code


def escuchar_o_escribir():
    print("\n🎙️ [COPILOTO] Escuchando orden... (presiona ENTER rápido para escribir en texto)")
    try:
        # Intento de captura de voz (timeout corto a 4s)
        raw = (
            subprocess.check_output(["termux-speech-to-text"], stderr=subprocess.DEVNULL, timeout=4)
            .decode("utf-8")
            .strip()
        )
        if raw:
            return raw.lower()
    except Exception:
        pass

    # Respaldo por consola en tiempo real
    print("⌨️ Entrada manual activada:")
    return input("Comandante > ").strip().lower()


def mapear_comando(texto):
    print(f'🗣️ Instrucción recibida: "{texto}"')

    # Comandos de sistema
    if "bateria" in texto or "energia" in texto:
        return "termux-battery-status"
    elif "memoria" in texto or "ram" in texto:
        return "free -m"
    elif "espacio" in texto or "disco" in texto:
        return "df -h ~/daniela-os"
    elif "ip" in texto or "red" in texto:
        return "ifconfig | grep 'inet '"
    elif "limpiar" in texto or "fotos" in texto:
        return "rm -f ~/daniela-os/*.jpg"
    elif "log" in texto or "registro" in texto:
        return "tail -n 20 ~/daniela-os/proactiva.log"
    elif "procesos" in texto:
        return "ps aux | grep python"

    # Comandos de Daniela OS
    elif "sos" in texto or "pánico" in texto:
        return "python ~/daniela-os/panic_sos.py"
    elif "notas" in texto:
        return "python ~/daniela-os/notas_proactivas.py listar"
    elif "tono vip" in texto:
        return "python ~/daniela-os/gestor_tonos.py LLAMADA_VIP"
    else:
        return None


def ejecutar_copiloto():
    texto = escuchar_o_escribir()
    if not texto:
        print("⚠️ No se ingresó ninguna instrucción.")
        return

    comando = mapear_comando(texto)

    if comando:
        print(f"⚡ [COMANDO GENERADO]: {comando}")
        run_bg(
            [
                "mpv",
                "--no-video",
                "--ao=opensles",
                "--volume=100",
                os.path.expanduser("~/daniela-os/sonidos/cyber_alarm.wav"),
            ]
        )
        print("--- SALIDA DEL SISTEMA ---")
        run_code(comando)
        print("--------------------------")
    else:
        print(f"❓ Instrucción no reconocida: '{texto}'")


if __name__ == "__main__":
    ejecutar_copiloto()

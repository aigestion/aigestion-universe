import subprocess
import sys


def execute_android_action(action_type, target=""):
    try:
        if action_type == "home":
            subprocess.run(
                ["termux-element-focus"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return "Navegando a la pantalla principal."
        elif action_type == "volume_up":
            subprocess.run(
                ["termux-volume", "music", "15"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "Volumen ajustado al máximo."
        elif action_type == "vibrate":
            subprocess.run(
                ["termux-vibrate", "-d", "300"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "Dispositivo vibrado."
        elif action_type == "battery":
            res = subprocess.run(["termux-battery-status"], capture_output=True, text=True)
            return f"Estado de batería: {res.stdout.strip()[:100]}"
    except Exception as e:
        return f"Error al ejecutar acción Android: {e}"
    return "Acción de control Android procesada."


if __name__ == "__main__":
    act = sys.argv[1] if len(sys.argv) > 1 else "vibrate"
    print(execute_android_action(act))

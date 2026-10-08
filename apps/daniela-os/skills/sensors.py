import json
import subprocess


def get_battery_status():
    try:
        res = subprocess.run(["termux-battery-status"], capture_output=True, text=True)
        data = json.loads(res.stdout)
        return f"Batería al {data['percentage']}% y {data['status'].lower()}."
    except Exception as e:
        return f"Error al leer sensor de batería: {e}"


def set_volume(level):
    try:
        subprocess.run(["termux-volume", "music", str(level)], capture_output=True)
        return f"Volumen ajustado al {level}%."
    except Exception as e:
        return f"Error al ajustar volumen: {e}"

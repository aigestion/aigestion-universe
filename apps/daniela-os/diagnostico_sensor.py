import json
import subprocess

try:
    raw = subprocess.check_output(
        ["termux-sensor", "-s", "accelerometer", "-n", "1"], stderr=subprocess.DEVNULL
    ).decode("utf-8")
    data = json.loads(raw)
    print("Datos brutos recibidos:")
    print(data)
    # Mostramos los valores limpios
    val = data.get("accelerometer", {}).get("values", [0, 0, 0])
    print(f"Valores procesados: X:{val[0]:.2f}, Y:{val[1]:.2f}, Z:{val[2]:.2f}")
except Exception as e:
    print(f"Error al leer sensor: {e}")

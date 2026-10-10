import json
import math
import subprocess

# Usamos el nombre exacto que mostró tu terminal
SENSOR_NAME = "LSM6DSV Accelerometer"

print(f"🕵️ Auditoría: Escuchando {SENSOR_NAME}...")
proc = subprocess.Popen(
    ["termux-sensor", "-s", SENSOR_NAME, "-d", "100"],
    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
)

last_acc = None
try:
    buffer = ""
    for line in iter(proc.stdout.readline, ''):
        buffer += line
        if "}" in line:
            try:
                data = json.loads(buffer)
                buffer = ""
                # Accedemos directamente a tu sensor
                if SENSOR_NAME in data:
                    vals = data[SENSOR_NAME].get("values", [])
                    if len(vals) == 3:
                        if last_acc:
                            delta = math.sqrt(sum((c - b)**2 for c, b in zip(vals, last_acc)))
                            # Imprimimos todo para ver qué pasa
                            print(f"Delta: {delta:.2f} | Vals: {vals}")
                            if delta > 3.0:
                                print("💥 ¡AGITE DETECTADO!")
                        last_acc = vals
            except Exception:
                buffer = ""
except KeyboardInterrupt:
    proc.terminate()

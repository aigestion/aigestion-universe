import json
import math
import subprocess
import time


def wait_for_shake_pixel(timeout=7):
    print("🖐️ [Sensor Pixel] Escuchando movimiento en tiempo real... ¡AGITA AHORA!")

    proc = subprocess.Popen(
        ["termux-sensor", "-s", "accelerometer", "-d", "50"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

    start_time = time.time()
    last_acc = None
    shaken = False
    buffer = ""

    try:
        while time.time() - start_time < timeout:
            line = proc.stdout.readline()
            if not line:
                continue

            buffer += line

            # Cada vez que se cierra una estructura JSON
            if "}" in line:
                try:
                    data = json.loads(buffer)
                    buffer = ""

                    # Buscar el objeto del acelerómetro en el diccionario
                    for _sensor_key, sensor_data in data.items():
                        if "values" in sensor_data:
                            vals = sensor_data["values"]
                            if len(vals) == 3:
                                if last_acc:
                                    delta = math.sqrt(sum((c - b)**2 for c, b in zip(vals, last_acc)))
                                    # Umbral súper sensible
                                    if delta > 3.5:
                                        print(f"💥 ¡AGITE DETECTADO! (Delta: {delta:.2f})")
                                        shaken = True
                                        break
                                last_acc = vals
                except Exception:
                    # Si aún no es un JSON válido, seguimos acumulando
                    pass

            if shaken:
                break
    finally:
        proc.terminate()
        proc.wait()

    return shaken

if __name__ == "__main__":
    if wait_for_shake_pixel(timeout=7):
        print("✔ ¡Perfecto! Detección de agite confirmada.")
    else:
        print("❌ Sin movimiento suficiente.")

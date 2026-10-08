import json
import os
import subprocess
import time

from monitor_recursos import autopurga_temporales, obtener_telemetria
from notas_proactivas import verificar_y_leer_notas
from verificar_rostro import verificar_usuario


def esta_moviendose():
    try:
        raw = subprocess.check_output(
            ["termux-sensor", "-s", "accelerometer", "-n", "1"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode("utf-8")
        data = json.loads(raw)

        sensor_data = data.get("accelerometer", {})
        if isinstance(sensor_data, list) and len(sensor_data) > 0:
            val = sensor_data[0].get("values", [0, 0, 0])
        elif isinstance(sensor_data, dict):
            val = sensor_data.get("values", [0, 0, 0])
        else:
            val = [0, 0, 0]

        return abs(val[0]) > 1.2 or abs(val[1]) > 1.2
    except Exception:
        return False


from safe_exec import run_bg


def check_presencia(telemetria):
    # Regla de Ahorro: Si la batería es inferior al 12% y no está cargando, se suspende la visión para proteger el teléfono
    if telemetria["pct"] < 12 and telemetria["estado"] == "UNPLUGGED":
        print("⚠️ [MODO SUPERVIVENCIA] Batería crítica (<12%). Reconocimiento facial pausado.")
        return False

    if esta_moviendose():
        # 1. Comprobar si es Alejandro (Comandante)
        if verificar_usuario() == 0:
            print("✅ Alejandro confirmado.")
            run_bg(
                [
                    "mpv",
                    "--no-video",
                    "--ao=opensles",
                    "--volume=100",
                    os.path.expanduser("~/daniela-os/sonidos/cyber_alarm.wav"),
                ]
            )
            return True
        else:
            # 2. Si no es el Comandante, verificar si es un familiar con nota pendiente
            verificar_y_leer_notas()
    return False


if __name__ == "__main__":
    print("🛡️ Daniela OS - Centinela Activo con Monitor de Recursos Integrado...")

    ciclos = 0
    while True:
        # Inspección de telemetría (batería, estado de carga y temperatura)
        telemetria = obtener_telemetria()

        # Alerta térmica preventiva en el bucle
        if telemetria["temp"] > 42.0:
            print(
                f"🔥 [ALERTA TÉRMICA] {telemetria['temp']}°C. Pausando red neuronal 10 segundos..."
            )
            time.sleep(10)
            continue

        if check_presencia(telemetria):
            time.sleep(8)  # Enfriamiento tras reconocimiento exitoso

        # Cada 10 ciclos de escaneo (~30 segundos), ejecutar autopurga de imágenes temporales
        ciclos += 1
        if ciclos >= 10:
            autopurga_temporales()
            ciclos = 0

        time.sleep(3)

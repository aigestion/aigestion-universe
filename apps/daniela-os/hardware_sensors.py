import json
import subprocess


def obtener_telemetria_hardware():
    try:
        resultado = subprocess.run(
            ["termux-battery-status"], capture_output=True, text=True, timeout=3
        )
        if resultado.returncode == 0:
            datos = json.loads(resultado.stdout)
            return {
                "bateria": datos.get("percentage", 0),
                "temperatura_c": datos.get("temperature", 0.0),
                "estado": datos.get("status", "DESCONOCIDO"),
            }
    except Exception as e:
        print(f"Error al leer batería: {e}")

    return {"bateria": 0, "temperatura_c": 0.0, "estado": "ERROR"}


if __name__ == "__main__":
    telemetria = obtener_telemetria_hardware()
    print(
        f"🔋 Batería: {telemetria['bateria']}% | Temp: {telemetria['temperatura_c']}°C | Estado: {telemetria['estado']}"
    )

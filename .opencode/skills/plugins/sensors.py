import subprocess
import json

def run(context):
    context.lower()
    
    try:
        # Lectura de sensores en tiempo real vía termux-sensor
        res = subprocess.run(
            ['termux-sensor', '-n', '1', '-s', 'light,accelerometer,gyroscope,pressure,ambient_temperature'],
            capture_output=True, text=True, timeout=6
        )
        output = res.stdout.strip()
        
        if not output:
            return "📡 [SENSORS]: No se obtuvo lectura de los sensores. Asegúrate de tener concedidos los permisos en Termux API."

        data = json.loads(output)
        reports = ["🌡️ *[TELEMETRÍA DE SENSORES]*\n"]

        # Procesamiento de lecturas según el tipo de sensor
        for sensor_name, values in data.items():
            val = values.get("values", [])
            if "light" in sensor_name.lower():
                lux = val[0] if val else "N/A"
                reports.append(f"💡 *Luz Ambiental:* `{lux} lux`")
            elif "accelerometer" in sensor_name.lower():
                if len(val) >= 3:
                    reports.append(f"📐 *Acelerómetro (X,Y,Z):* `{val[0]:.2f}, {val[1]:.2f}, {val[2]:.2f}`")
            elif "gyroscope" in sensor_name.lower():
                if len(val) >= 3:
                    reports.append(f"🔄 *Giroscopio (X,Y,Z):* `{val[0]:.2f}, {val[1]:.2f}, {val[2]:.2f}`")
            elif "pressure" in sensor_name.lower():
                p = val[0] if val else "N/A"
                reports.append(f"⏱️ *Presión Atmosférica:* `{p} hPa`")
            elif "temperature" in sensor_name.lower():
                temp = val[0] if val else "N/A"
                reports.append(f"🌡️ *Temperatura Ambiental:* `{temp} °C`")

        if len(reports) == 1:
            return f"📡 [SENSORS]: Datos crudos recibidos:\n```json\n{output[:500]}\n```"

        return "\n".join(reports)

    except FileNotFoundError:
        return "❌ [SENSORS]: No se encuentra 'termux-sensor'. Verifica tener instalado el paquete 'termux-api'."
    except Exception as e:
        return f"❌ [SENSORS]: Error al leer sensores: {str(e)}"

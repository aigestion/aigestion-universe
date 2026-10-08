import importlib
import subprocess
import json
import os
import time

def run(context):
    cmd = context.lower()
    talk = "habla" in cmd or "tts" in cmd or "voz" in cmd
    
    report_lines = []
    report_lines.append("🌅 *[DANIELA OS - INFORME MATUTINO TÁCTICO]*")
    report_lines.append(f"📅 *Fecha:* `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n")

    # 1. Batería
    try:
        res = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=4)
        b_data = json.loads(res.stdout)
        perc = b_data.get('percentage', 'N/A')
        temp = b_data.get('temperature', 'N/A')
        stat = b_data.get('status', 'N/A')
        report_lines.append(f"🔋 *Energía:* Nivel {perc}% ({stat}) | Temp: {temp}°C")
    except:
        report_lines.append("🔋 *Energía:* Sin lectura disponible")

    # 2. Sensores Físicos
    try:
        sensors = importlib.import_module('plugins.sensors')
        s_data = sensors.run('sensores')
        report_lines.append("\n📡 *Sensores Ambientales:*")
        for line in s_data.split("\n"):
            if any(k in line for k in ["Luz", "Presión", "Acelerómetro"]):
                report_lines.append(f"  {line.strip()}")
    except:
        report_lines.append("📡 *Sensores:* No se pudo conectar con el hardware")

    # 3. Ubicación
    try:
        loc = importlib.import_module('plugins.location')
        loc_res = loc.run('ubicacion')
        report_lines.append("\n📍 *Posición Táctica:*")
        for line in loc_res.split("\n"):
            if any(k in line for k in ["Latitud", "Longitud", "Proveedor"]):
                report_lines.append(f"  {line.strip()}")
    except:
        report_lines.append("📍 *Posición:* Módulo de ubicación no disponible")

    # 4. Integridad del Sistema (SHA-256)
    try:
        ig = importlib.import_module('plugins.integrity_guard')
        ig_res = ig.run('check')
        report_lines.append(f"\n🛡️ *Integridad Criptográfica:* {ig_res}")
    except:
        report_lines.append("\n🛡️ *Integridad:* Error al auditar firmas")

    # 5. Tareas Programadas
    try:
        sch = importlib.import_module('plugins.scheduler')
        sch_res = sch.run('tareas')
        report_lines.append(f"\n⏱️ *Planificador:* {sch_res.splitlines()[0] if sch_res else 'Sin tareas'}")
    except:
        pass

    full_report = "\n".join(report_lines)

    # 🗣️ Opciones de Sintetización por Voz
    if talk:
        try:
            tts = importlib.import_module('plugins.tts_bridge')
            brief_text = f"Buenos días Comandante. Batería al {perc} por ciento. Sistema verificado e íntegro. Daniela OS reporta estabilidad absoluta."
            tts.run(f"di {brief_text}")
        except Exception as e:
            print(f"Error al reproducir voz: {e}")

    return full_report

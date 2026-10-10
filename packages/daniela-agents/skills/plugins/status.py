import subprocess
import json
import importlib

def run(context):
    report = ["📊 *[DANIELA OS - INFORME DE ESTADO]*\n"]
    
    # 1. Batería Hardware
    try:
        res = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=5)
        data = json.loads(res.stdout)
        perc = data.get("percentage", "N/A")
        health = data.get("health", "N/A")
        temp = data.get("temperature", "N/A")
        report.append(f"🔋 *Batería:* {perc}% | Salud: {health} | Temp: {temp}°C")
    except Exception as e:
        report.append(f"🔋 *Batería:* Error al consultar ({e})")

    # 2. Registros de Memoria
    try:
        mem = importlib.import_module('plugins.memory')
        vault = mem.load_vault()
        report.append(f"💾 *Bóveda de Memoria:* {len(vault)} registro(s) almacenado(s)")
    except Exception as e:
        report.append(f"💾 *Bóveda de Memoria:* No disponible ({e})")

    # 3. Tareas Programadas
    try:
        sch = importlib.import_module('plugins.scheduler')
        tasks = sch.load_tasks()
        report.append(f"⏱️ *Planificador:* {len(tasks)} tarea(s) activa(s)")
    except Exception as e:
        report.append(f"⏱️ *Planificador:* No disponible ({e})")

    # 4. Estado de Conexión y Red
    try:
        res_net = subprocess.run(['ip', 'neighbor'], capture_output=True, text=True, timeout=5)
        active_devs = [l for l in res_net.stdout.strip().split('\n') if 'REACHABLE' in l or 'STALE' in l]
        report.append(f"📡 *Red Local:* {len(active_devs)} dispositivo(s) detectado(s)")
    except Exception:
        report.append("📡 *Red Local:* Sin datos de red")

    return "\n".join(report)

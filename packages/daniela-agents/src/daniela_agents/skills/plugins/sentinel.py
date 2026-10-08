import subprocess
import json
import importlib
import threading

def run_async(func, *args):
    thread = threading.Thread(target=func, args=args, daemon=True)
    thread.start()

def execute_chain_reactions(sec_cam):
    try:
        analysis = sec_cam.run("snap")
        try:
            notifier = importlib.import_module('plugins.notifier')
            notifier.run(f"🚨 INTRUSO DETECTADO | {analysis[:80]}...")
        except: pass
        try:
            tts = importlib.import_module('plugins.tts_bridge')
            tts.run("di Advertencia. Intruso detectado.")
        except: pass
        try:
            loc = importlib.import_module('plugins.location')
            loc.run("ubicacion guarda")
        except: pass
    except Exception as e:
        print(f"Error en reacción: {e}")

def run(context):
    # 1. Batería Baja / Gestión Energética Automática (18% actual)
    try:
        res = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=3)
        data = json.loads(res.stdout)
        percentage = data.get('percentage', 100)
        status = data.get('status', '')
        
        if percentage <= 20 and status == 'DISCHARGING':
            try:
                ps = importlib.import_module('plugins.power_saver')
                ps.run("auto")
            except: pass
    except: pass

    # 2. Detección de Movimiento
    try:
        sec_cam = importlib.import_module('plugins.security_cam')
        if sec_cam.check_movement(threshold=3.5):
            run_async(execute_chain_reactions, sec_cam)
            return "🚨 [SENTINEL]: Movimiento anómalo. Protocolo activado."
    except: pass

    # 3. Auditoría de Integridad
    try:
        ig = importlib.import_module('plugins.integrity_guard')
        alert = ig.verify_integrity()
        if alert: return alert
    except: pass

    # 4. Scheduler
    try:
        sch = importlib.import_module('plugins.scheduler')
        sch.check_and_execute_due_tasks()
    except: pass
    
    return "✅ Sistema estable (Modo Ahorro Velando)."

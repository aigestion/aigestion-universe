import os

filepath = "app_daniela.py"

if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        code = f.read()

    proactive_backend = """
# --- DANIELA PROACTIVE ENGINE ---
import threading
import time

def monitor_proactivo_loop():
    while True:
        try:
            # Comprobar eventos de telemetría o avisos pendientes
            if os.path.exists("alertas_pendientes.json"):
                pass
            time.sleep(15)
        except Exception:
            pass

# Iniciar hilo de vigilancia proactiva
threading.Thread(target=monitor_proactivo_loop, daemon=True).start()
# --- END PROACTIVE ENGINE ---
"""

    if "DANIELA PROACTIVE ENGINE" not in code:
        code += "\n" + proactive_backend
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Motor proactivo de fondo inyectado en app_daniela.py")
    else:
        print("ℹ️ El motor proactivo ya está activo en el backend.")

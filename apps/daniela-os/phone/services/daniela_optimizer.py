import os
import subprocess
import time

# 1. Definir directorio de RAM temporal en Termux para E/S ultra rápida
RAM_BUFFER_DIR = "/data/data/com.termux/files/usr/tmp/daniela_ram"


def setup_ram_buffer():
    """Crea un búfer en memoria RAM para no desgastar la memoria flash UFS."""
    if not os.path.exists(RAM_BUFFER_DIR):
        os.makedirs(RAM_BUFFER_DIR, exist_ok=True)
    print(f"⚡ [RAM BUFFER]: Búfer de audio activado en: {RAM_BUFFER_DIR}")


def optimize_process_priority():
    """Asigna prioridades altas (renice -10) a los servicios críticos de Daniela."""
    targets = ["daniela_router.py", "daniela_edge_suite.py", "daniela_wakeword.py"]
    optimized = 0

    for target in targets:
        try:
            # Obtener PIDs del proceso
            res = subprocess.run(["pgrep", "-f", target], capture_output=True, text=True)
            pids = res.stdout.strip().split()

            for pid in pids:
                if pid:
                    # Aplicar alta prioridad (renice)
                    subprocess.run(
                        ["renice", "-n", "-10", "-p", pid],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    optimized += 1
        except Exception:
            pass

    print(f"🚀 [CPU SCHEDULER]: {optimized} procesos elevados a alta prioridad (-10).")


def run_garbage_collector():
    """Limpia archivos temporales de audio en RAM con más de 5 minutos de antigüedad."""
    now = time.time()
    cleaned = 0
    if os.path.exists(RAM_BUFFER_DIR):
        for f in os.listdir(RAM_BUFFER_DIR):
            fp = os.path.join(RAM_BUFFER_DIR, f)
            if os.path.isfile(fp) and (now - os.path.getmtime(fp)) > 300:
                os.remove(fp)
                cleaned += 1
    if cleaned > 0:
        print(f"🧹 [RAM CLEANER]: {cleaned} archivos temporales purgados de la memoria.")


if __name__ == "__main__":
    setup_ram_buffer()
    optimize_process_priority()
    run_garbage_collector()

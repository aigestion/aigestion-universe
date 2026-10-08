import json
import os
import subprocess


def get_system_health():
    """
    Skill #28: Resource & Battery Optimizer.
    Recopila métricas de RAM, batería y temperatura para optimizar recursos.
    """
    metrics = {}
    try:
        # Batería vía Termux API
        bat_out = subprocess.check_output(["termux-battery-status"], text=True)
        bat_data = json.loads(bat_out)
        metrics['battery'] = f"{bat_data.get('percentage', 0)}%"
        metrics['temperature'] = f"{bat_data.get('temperature', 0)}°C"
        metrics['status'] = bat_data.get('status', 'Unknown')
    except Exception:
        metrics['battery'] = "N/A"
        metrics['temperature'] = "N/A"
        metrics['status'] = "N/A"

    try:
        # Memoria RAM libre
        free_out = subprocess.check_output(["free", "-m"], text=True)
        lines = free_out.strip().split('\n')
        if len(lines) > 1:
            ram_parts = lines[1].split()
            metrics['ram_used'] = f"{ram_parts[2]}MB"
            metrics['ram_total'] = f"{ram_parts[1]}MB"
    except Exception:
        metrics['ram_used'] = "N/A"

    return f"⚡ [HEALTH OPTIMIZER]: Batería: {metrics.get('battery')} ({metrics.get('status')}) | Temp: {metrics.get('temperature')} | RAM Usada: {metrics.get('ram_used', 'N/A')}/{metrics.get('ram_total', 'N/A')}"

def optimize_resources():
    """Limpia caché temporal y procesos huérfanos para reducir consumo."""
    try:
        # Limpieza de caché tmp interna
        tmp_dir = os.path.expanduser("~/daniela-os/static/")
        cleaned = 0
        for f in os.listdir(tmp_dir):
            if f.startswith(("security_alert", "live_frame")):
                os.remove(os.path.join(tmp_dir, f))
                cleaned += 1
        return f"🧹 [OPTIMIZER]: Recursos liberados. {cleaned} archivo(s) temporales eliminados."
    except Exception as e:
        return f"⚠️ [OPTIMIZER ERROR]: {e}"

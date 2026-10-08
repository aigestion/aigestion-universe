import json

import psutil
from safe_exec import run_cmd, run_out


def send_haptic_feedback(duration_ms=100):
    try:
        run_cmd(f"termux-vibrate -d {duration_ms}", timeout=1)
    except Exception:
        pass


def send_android_notification(title, content):
    try:
        run_cmd(
            f"termux-notification --title '{title}' --content '{content}' --priority high",
            timeout=2,
        )
    except Exception:
        pass


def scan_local_network():
    try:
        res = run_cmd("arp -a", timeout=3)
        return res.stdout if res.stdout else "No dispositivos."
    except Exception:
        return "Error red."


def get_battery_status():
    try:
        res = run_cmd("termux-battery-status", timeout=2)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception:
        pass
    return {"percentage": 0}


def execute_shell(command):
    try:
        result = run_cmd(command, timeout=5)
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error: {e}"


def get_git_info():
    try:
        commit = run_out("git log -1 --pretty=format:'%h'").strip()
        return {"commit": commit}
    except Exception:
        return {"commit": "N/A"}


def get_system_status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "ram_porcentaje": f"{memory.percent}%",
        "disco_libre_gb": round(disk.free / (1024**3), 2),
        "bateria": get_battery_status().get("percentage", 0),
        "git": get_git_info(),
    }

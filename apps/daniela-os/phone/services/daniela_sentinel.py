import json
import os
import subprocess
import time

LOG_FILE = os.path.expanduser("~/logs/sentinel.log")


def get_battery_info():
    try:
        res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return {
                "percentage": data.get("percentage", 100),
                "temperature": data.get("temperature", 0.0),
                "plugged": data.get("plugged", "UNPLUGGED"),
            }
    except Exception:
        pass
    return {"percentage": 100, "temperature": 30.0, "plugged": "UNPLUGGED"}


def evaluate_performance_profile():
    info = get_battery_info()
    pct = info["percentage"]
    temp = info["temperature"]
    plugged = info["plugged"]

    profile = "NORMAL"
    reason = "Parámetros nominales."

    # Lógica de protección térmica y energética
    if temp >= 42.0:
        profile = "ECO_COOLING"
        reason = f"Temperatura elevada ({temp}°C). Reduciendo carga local."
    elif pct <= 15 and plugged == "UNPLUGGED":
        profile = "ECO_SAVER"
        reason = f"Batería crítica ({pct}%). Desactivando servicios secundarios."
    elif plugged != "UNPLUGGED":
        profile = "HIGH_PERFORMANCE"
        reason = "Dispositivo conectado a energía. Rendimiento máximo."

    status = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "battery_pct": pct,
        "temperature": temp,
        "power_source": plugged,
        "active_profile": profile,
        "reason": reason,
    }

    os.makedirs(os.path.expanduser("~/logs"), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{status['timestamp']}] Profile: {profile} | Temp: {temp}°C | Batt: {pct}%\n")

    return status


if __name__ == "__main__":
    status = evaluate_performance_profile()
    print(f"📊 [DANIELA SENTINEL]: Perfil Activo -> {status['active_profile']}")
    print(f"   • Temperatura: {status['temperature']}°C")
    print(f"   • Batería: {status['battery_pct']}% ({status['power_source']})")
    print(f"   • Estado: {status['reason']}")
